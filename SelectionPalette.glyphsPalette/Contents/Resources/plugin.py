# encoding: utf-8

from __future__ import print_function
from enum import Enum
from importlib.metadata import distribution
import objc
from AppKit import NSMenuItem, NSImage, NSAlternateKeyMask, NSCommandKeyMask
from GlyphsApp import *
from GlyphsApp import Glyphs, EDIT_MENU, LINE, CURVE, OFFCURVE
from GlyphsApp.plugins import *
from vanilla import Window, ImageButton, Group, TextBox, VerticalStackView, HorizontalStackView, ImageView, HorizontalLine
import traceback, os

# 
# Translations
# 

translations = {
	"undo_selection": Glyphs.localize({ 'en': "Undo Selection" }),
	"shrink_selection": Glyphs.localize({ 'en': "Shrink Selection" }),
	"select_between": Glyphs.localize({ 'en': "Select Between" }),
	"grow_selection": Glyphs.localize({ 'en': "Grow Selection" }),
	"continue_selection": Glyphs.localize({ 'en': "Continue Selection", "de": "Auswahl fortsetzen" }),
	"select_linked_hints": Glyphs.localize({ 'en': "Select Linked Hints" }),
	"boolean_add": lambda label: Glyphs.localize({'en': "Add %s to selection" % label,}),
	"boolean_remove": lambda label: Glyphs.localize({'en': "Remove %s from selection" % label,}),
	"boolean_intersect": lambda label: Glyphs.localize({'en': "Select only %s" % label,}),
}

class Operation(Enum):
	ADD = 0
	SUBTRACT = 1
	INTERSECT = 2

def getImageViewFromPath(path):
	osource_image = os.path.join(os.path.dirname(__file__), path + '.svg')
	icon = NSImage.alloc().initWithContentsOfFile_(osource_image)
	icon.setTemplate_(True)
	return icon

# createImageButton def with 3 named arguments for icon, callback and tooltip
def createImageButton(icon, callback, tooltip):
	addButton = ImageButton(
		"auto",
		bordered=False,
		imageObject=icon,
		callback=callback,
	)
	addButton.getNSButton().setToolTip_(tooltip)
	return addButton

class SelectionPalette(PalettePlugin):
	def settings(self):
		try:
			self.name = "SelectionPalette"
			# cache for vanilla buttons https://github.com/robotools/vanilla/issues/165
			self.buttonList = []
			# TODO width does not update on panel resize
			self.width = 160
			self.height = 185
			types = (
				("SmoothCurves", "Smooth", self.selectSmoothCurves_withOperation_),
				("SharpCurves", "Sharp", self.selectSharpCurves_withOperation_),
				("Lines", "Lines", self.selectLines_withOperation_),
				("Handles", "Handles", self.selectHandles_withOperation_),
				("Components", "Components", self.selectComponents_withOperation_),
				("Anchors", "Anchors", self.selectAnchors_withOperation_),
				("Guides", "Guides", self.selectGuides_withOperation_),
				)
			self.paletteView = Window((self.width, self.height))
			self.paletteView.group = Group((0, 0, self.width, self.height))
			self.paletteView.group.stack = VerticalStackView((0, 0, self.width, self.height), views=[], spacing=4, edgeInsets=(4, 8, 8, 8), distribution="gravity", alignment="center")

			addIcon = getImageViewFromPath('Union')
			subtractIcon = getImageViewFromPath('Subtract')
			intersectIcon = getImageViewFromPath('Intersect')
			for type,label,callback in types:
				addButton = createImageButton(
					icon=addIcon,
					callback=lambda sender, callback=callback: callback(sender, Operation.ADD),
					tooltip=translations["boolean_add"](label)
				)
				subtractButton = createImageButton(
					icon=subtractIcon,
					callback=lambda sender, callback=callback: callback(sender, Operation.SUBTRACT),
					tooltip=translations["boolean_remove"](label)
				)
				intersectionButton = createImageButton(
					icon=intersectIcon,
					callback=lambda sender, callback=callback: callback(sender, Operation.INTERSECT),
					tooltip=translations["boolean_intersect"](label)
				)
				
				self.buttonList.extend([addButton, subtractButton, intersectionButton])
				
				rowIcon = getImageViewFromPath(type)
				rowImageView = ImageView((0, 0, 32, 32))
				rowImageView.setImage(imageObject=rowIcon)
				row = HorizontalStackView(
					(0, 0, self.width, 0), 
					views=[
						dict(view=rowImageView, width=22),
						# dict(view=TextBox("auto", text=label, sizeStyle="small"), width=72),
						dict(view=HorizontalStackView(
							(0, 0, 12, 0),
							views=[
								dict(view=addButton),
								dict(view=subtractButton),
								dict(view=intersectionButton),
							],
							spacing=8,
						)),
					],
					spacing=24,
					distribution="equalSpacing",
					alignment="leading",
					edgeInsets=(0, 0, 0, 0),
				)
				self.paletteView.group.stack.appendView(row)

			# Set dialog to NSView
			self.dialog = self.paletteView.group.getNSView()

		except:
			print(traceback.format_exc())
	def start(self):
		self.addMenuItems()

	def addMenuItems(self):
		# Edit menu additions
		try:
			# TODO: feel like I shouldn't have to do this, but otherwise menus are added for each document, because of the loop below? unsure
			if (Glyphs.menu[EDIT_MENU].submenu().indexOfItemWithTitle_(translations["continue_selection"]) > 0):
				return

			# TODO We can add menu items near the selection section, but this methoddoes not work for locales other than English 👎 fallback to end of menu
			selectionItemIndex = Glyphs.menu[EDIT_MENU].submenu().indexOfItemWithTitle_("Keep Layer Selections in Sync")
			if (selectionItemIndex < 0):
				selectionItemIndex = Glyphs.menu[EDIT_MENU].submenu().numberOfItems() - 1
			selectionItemIndex += 1
			Glyphs.menu[EDIT_MENU].submenu().insertItem_atIndex_(NSMenuItem.separatorItem(), selectionItemIndex)
			selectionItemIndex += 1
			menuItems = (
				(translations["undo_selection"],      self.undoSelection_,     "Undo",     "["),
				(translations["shrink_selection"],    self.shrinkSelection_,   "Shrink",   "-"),
				(translations["select_between"],      self.fillSelection_,     "Between",  ":"),
				(translations["grow_selection"],      self.growSelection_,     "Grow",     "+"),
				(translations["continue_selection"],  self.continueSelection_, "Continue", "]"),
				(translations["select_linked_hints"], self.selectLinkedHints_, "Corners",  "<"),
			)
			for menuItemLabel,menuItemCallback,menuItemIconKey,menuItemKey in menuItems:
				item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(menuItemLabel, menuItemCallback, menuItemKey)
				item.setKeyEquivalentModifierMask_(NSAlternateKeyMask | NSCommandKeyMask)
				item.setTarget_(self)
				Glyphs.menu[EDIT_MENU].submenu().insertItem_atIndex_(item, selectionItemIndex)
				selectionItemIndex += 1
		except:
			print(traceback.format_exc())
			
	# Helpers
	def layer(self):
		return Glyphs.font.selectedLayers[0]
	@objc.python_method
	def getSibling(self, node, next):
		path = node.parent
		length = len(path.nodes)
		siblingIndex = 0
		crossesBounds = False
		
		if next == True:
			siblingIndex = (node.index + 1) % length
			if siblingIndex == 0:
				crossesBounds = True
		else:
			siblingIndex = (node.index - 1 + length) % length
			if siblingIndex == length - 1:
				crossesBounds = True
		
		if not path.closed and crossesBounds:
			return node
		else:
			return path.nodes[siblingIndex]
	@objc.python_method
	def nextNode(self, node):
		return self.getSibling(node, True)
	@objc.python_method
	def prevNode(self, node):
		return self.getSibling(node, False)
	
	# 
	# Selection methods
	# 
	def continueSelection_(self, sender):
		try:
			#  Need at least two nodes to infer a pattern
			if len(self.layer().selection) >= 2:
				lastNode = self.layer().selection[-1]
				originNode = self.layer().selection[-2]
				
				# TODO make sure https://github.com/danielgamage/SelectionPalette/issues/8 doesn't regress
				# Ensure that the last two nodes are on the same path
				if (lastNode.parent == originNode.parent):
					# Get difference of two nodes
					if lastNode.index > originNode.index:
						# normal diff
						rhythm = lastNode.index - originNode.index
					else:
						# crossing bounds of path
						rhythm = abs(originNode.index - len(originNode.parent.nodes)) + lastNode.index

					# Move to node width rhythm
					nodeToSelect = lastNode
					i = 0
					while i < rhythm:
						nodeToSelect = nodeToSelect.nextNode
						i += 1

					# Select it
					nodeToSelect.selected = True
		except:
			print(traceback.format_exc())
	def undoSelection_(self, sender):
		try: 
			# Get last-selected node
			lastNode = self.layer().selection[-1]

			# Deselect it
			lastNode.selected = False
		except:
			print(traceback.format_exc())
	def growSelection_(self, sender):
		try:
			nodesToSelect = []

			# Get nodes on outside edges of selection
			for path in self.layer().paths:
				for node in path.nodes:
					if not node.selected:
						if self.nextNode(node).selected or self.prevNode(node).selected:
							nodesToSelect.append(node)

			self.selectElements_(nodesToSelect)
		except:
			print(traceback.format_exc())
	def shrinkSelection_(self, sender):
		try:
			nodesToDeselect = []

			# Get nodes on inside edges of selection
			for path in self.layer().paths:
				for node in path.nodes:
					if node.selected:
						if not self.nextNode(node).selected or not self.prevNode(node).selected:
							nodesToDeselect.append(node)

			self.deselectElements_(nodesToDeselect)
		except:
			print(traceback.format_exc())
	def fillSelection_(self, sender):
		try:
			nodesToSelect = []

			lastNode = self.layer().selection[-1]
			originNode = self.layer().selection[-2]

			# only allow filling if nodes are on same path
			if (lastNode.parent == originNode.parent):
				path = lastNode.parent

				# sort nodes by index
				if (lastNode.index > originNode.index):
					node1 = originNode
					node2 = lastNode
				else:
					node1 = lastNode
					node2 = originNode

				if ((not path.closed) or (node2.index - node1.index <= node1.index + len(path.nodes) - node2.index)):
					# shortest (or only) path is direct from node 1 to node 2
					nodesToSelect.extend(path.nodes[node1.index:node2.index])
				else:
					# shortest path crosses path bounds
					nodesToSelect.extend(path.nodes[0:node1.index])
					nodesToSelect.extend(path.nodes[node2.index:-node2.index])

				self.selectElements_(nodesToSelect)
		except:
			print(traceback.format_exc())

	# 
	# Selection utils
	# 
	def selectElements_withBooleanOperation_(self, elements, booleanOperation):
		try:
			self.layer().beginChanges()
			for element in elements:
				element.selected = booleanOperation
			self.layer().endChanges()
			# Glyphs.font.currentTab.redraw()
		except:
			print(traceback.format_exc())
	def selectElements_(self, elements):
		self.selectElements_withBooleanOperation_(elements, True)
	def deselectElements_(self, elements):
		self.selectElements_withBooleanOperation_(elements, False)

	def performSelectionOnArray_andOperation_(self, selectionArray, operation):
		try:
			if operation == Operation.ADD:
				self.selectElements_(selectionArray)
			elif operation == Operation.SUBTRACT:
				self.deselectElements_(selectionArray)
			elif operation == Operation.INTERSECT:
				elementsToDeselect = []
				for element in self.layer().selection:
					if not element in selectionArray:
						elementsToDeselect.append(element)
				self.deselectElements_(elementsToDeselect)
		except:
			print(traceback.format_exc())

	def selectNodesByType_andSmooth_withOperation_(self, type, smooth, operation):
		try:
			selectionArray = []

			# Get nodes on outside edges of selection
			for path in self.layer().paths:
				for node in path.nodes:
					conditions = []
					
					if type:
						# TODO when looking for lines, ignore ends of open paths that neighbor an OFFCURVE
						# when looking for sharp curves, add sharp lines that neighbor offcurves
						curvish = type == CURVE and node.type == LINE and not node.smooth and (self.prevNode(node).type == OFFCURVE or self.nextNode(node).type == OFFCURVE)
						if curvish:
							conditions.append(True)
						else:
							conditions.append(node.type == type)
					if smooth is not None:
						conditions.append(node.smooth == smooth)

					# if all conditions pass...
					if all(conditions):
						selectionArray.append(node)
						# if looking for LINEs, select node (unless it's OFFCURVE)'s prevNode as well
						if type == LINE and node.type == LINE:
							if self.prevNode(node) and self.prevNode(node).type != OFFCURVE:
								selectionArray.append(self.prevNode(node))
						# if looking for LINEs, add next (non-offcurve) node
						if type == LINE and self.nextNode(node).type != OFFCURVE:
							selectionArray.append(self.nextNode(node))
					

			# Select them
			self.performSelectionOnArray_andOperation_(selectionArray, operation)
		except:
			print(traceback.format_exc())
	
	# 
	# Selection Types
	# 
	def selectSmoothCurves_withOperation_(self, sender, operation):
		# should select both line and curve nodes with smooth connections
		self.selectNodesByType_andSmooth_withOperation_(None, True, operation)
	def selectSharpCurves_withOperation_(self, sender, operation):
		self.selectNodesByType_andSmooth_withOperation_(CURVE, False, operation)
	def selectLines_withOperation_(self, sender, operation):
		self.selectNodesByType_andSmooth_withOperation_(LINE, None, operation)
	def selectHandles_withOperation_(self, sender, operation):
		self.selectNodesByType_andSmooth_withOperation_(OFFCURVE, None, operation)
	def selectAnchors_withOperation_(self, sender, operation):
		selectionArray = []
		anchors = self.layer().anchors
		for anchor in anchors:
			selectionArray.append(anchor)
		self.performSelectionOnArray_andOperation_(selectionArray, operation)

	def selectComponents_withOperation_(self, sender, operation):
		selectionArray = []
		for component in self.layer().components:
			selectionArray.append(component)
		self.performSelectionOnArray_andOperation_(selectionArray, operation)
	def selectGuides_withOperation_(self, sender, operation):
		try:
			selectionArray = []

			# Currently disabled because 
			# globalGuides = Glyphs.font.selectedFontMaster.guides
			# selectionArray.extend(globalGuides) 
			localGuides = self.layer().guides
			selectionArray.extend(localGuides)

			self.performSelectionOnArray_andOperation_(selectionArray, operation)
		except:
			print(traceback.format_exc())

	# 
	# Transfers
	# 
	
	# Transfers selection from origin nodes to their connected corner components, caps, brushes(?)
	def selectLinkedHints_(self, sender):
		hints = self.layer().hints
		deselectionArray = []
		selectionArray = []
		for element in self.layer().selection:
			for hint in hints:
				if hint.originNode == element or hint.targetNode == element:
					deselectionArray.append(element)
					selectionArray.append(hint)
			
		for element in deselectionArray:
			element.selected = False
		for element in selectionArray:
			element.selected = True
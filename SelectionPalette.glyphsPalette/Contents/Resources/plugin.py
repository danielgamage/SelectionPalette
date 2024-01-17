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
from math import atan2, pi

# 
# Translations
# 

translations = {
	"undo_selection": Glyphs.localize({ 'en': "Undo Selection" }),
	"shrink_selection": Glyphs.localize({ 'en': "Shrink Selection" }),
	"select_between": Glyphs.localize({ 'en': "Select Between" }),
	"grow_selection": Glyphs.localize({ 'en': "Grow Selection" }),
	"continue_selection": Glyphs.localize({ 'en': "Continue Selection", "de": "Auswahl fortsetzen" }),
	"select_linked_hints": Glyphs.localize({ 'en': "Select Linked Caps/Corners" }),
	"select_extremes": Glyphs.localize({ 'en': "Select Extremes" }),
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

# utils
getAngleBetweenPoints = lambda p1, p2: atan2(p2.y - p1.y, p2.x - p1.x) * 180 / pi
isMultipleOf90 = lambda angle: (angle + 360) % 90 == 0

def is_node_extreme(node):
	if (node.type == CURVE or node.type == LINE) and (node.prevNode.type == OFFCURVE or node.nextNode.type == OFFCURVE):
			# Calculate the angles
			angle1 = getAngleBetweenPoints(node.prevNode, node)
			angle2 = getAngleBetweenPoints(node, node.nextNode)

			is_extreme = angle1 == angle2 and isMultipleOf90(angle1)
			return is_extreme

class SelectionPalette(PalettePlugin):
	def settings(self):
		try:
			self.name = "SelectionPalette"
			# cache for vanilla buttons https://github.com/robotools/vanilla/issues/165
			self.buttonList = []
			# TODO width does not update on panel resize
			self.width = 180
			self.height = 185
			types = (
				("SmoothCurves", "Smooth", self.selectSmoothCurves_withOperation_, [
					"All",
					"Extremes",
					"NonExtremes",
				]),
				("SharpCurves", "Sharp", self.selectSharpCurves_withOperation_, [
					"All",
					"Extremes",
					"NonExtremes",
				]),
				("Lines", "Lines", self.selectLines_withOperation_, [
					"All",
					"Extremes",
					"NonExtremes",
				]),
				("Handles", "Handles", self.selectHandles_withOperation_, [
					"All",
					"Extremes",
					"NonExtremes",
				]),
				("Components", "Components", self.selectComponents_withOperation_, [
					"All",
					"Locked",
					"Unlocked",
				]),
				("Anchors", "Anchors", self.selectAnchors_withOperation_, [
					"All",
					"Anchors",
					"UnderscoredAnchors",
					"Entry",
					"Exit",
				]),
				("Guides", "Guides", self.selectGuides_withOperation_, [
					"Unlocked",
					"Locked",
					"Global",
					"Local",
					"All",
				]),
				)
			# generate list from types
			self.rowSettings = list(map(lambda type: {
				"icon": getImageViewFromPath(type[0]),
				"label": type[1],
				"callback": type[2],
				"options": type[3],
				"option": 0,
				"enabled": True,
			}, types))
			self.paletteView = Window((self.width, self.height))
			self.paletteView.group = Group((0, 0, self.width, self.height))
			self.paletteView.group.stack = VerticalStackView((0, 0, self.width, self.height), views=[], spacing=4, edgeInsets=(4, 8, 8, 8), distribution="gravity", alignment="center")

			addIcon = getImageViewFromPath('Union')
			subtractIcon = getImageViewFromPath('Subtract')
			intersectIcon = getImageViewFromPath('Intersect')
			for idx, (type,label,callback,options) in enumerate(types):
				print(idx, type, label, callback, options)
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
				
				selectedOption = options[self.rowSettings[idx]["option"]]
				rowModifierIcon = getImageViewFromPath("Icon=" + selectedOption)
				
				optionButton = createImageButton(
					icon=rowModifierIcon,
					# add 1 to the current rowSettings item's option
					callback=lambda sender, callback=callback, idx=idx: self.updateOption(sender, callback, idx),
					tooltip=translations["boolean_intersect"](label)
				)
				
				self.buttonList.extend([addButton, subtractButton, intersectionButton, optionButton])
				
				rowIcon = getImageViewFromPath(type)
				rowImageView = ImageView((0, 0, 32, 32))
				rowImageView.setImage(imageObject=rowIcon)
				row = HorizontalStackView(
					(0, 0, self.width, 0), 
					views=[
						# dict(view=TextBox("auto", text=label, sizeStyle="small"), width=72),
						dict(view=HorizontalStackView(
							(0, 0, 32, 0), 
							views=[
								dict(view=rowImageView, width=22),
								dict(view=optionButton),
							],
							spacing=4,
							alignment="center",
							edgeInsets=(0, 0, 0, 0),
						)),
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
					spacing=16,
					distribution="equalSpacing",
					alignment="center",
					edgeInsets=(0, 0, 0, 0),
				)
				self.paletteView.group.stack.appendView(row)

			# Set dialog to NSView
			self.dialog = self.paletteView.group.getNSView()

		except:
			print(traceback.format_exc())
	def start(self):
		self.addMenuItems()
		
	@objc.python_method
	def updateOption(self, sender, callback, idx):
		try:
			direction = -1 if Glyphs.currentDocument.windowController().AltKey() else 1
			optionsLength = len(self.rowSettings[idx]["options"])
			self.rowSettings[idx]["option"] = (self.rowSettings[idx]["option"] + direction + optionsLength) % optionsLength
			selectedOption = self.rowSettings[idx]["options"][self.rowSettings[idx]["option"]]
			rowModifierIcon = getImageViewFromPath("Icon=" + selectedOption)
			sender.setImage(imageObject=rowModifierIcon)
		except:
			print(traceback.format_exc())

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
				(translations["undo_selection"],          self.undoSelection_,          "Undo",     "["),
				(translations["continue_selection"],      self.continueSelection_,      "Continue", "]"),
				(translations["shrink_selection"],        self.shrinkSelection_,        "Shrink",   "-"),
				(translations["grow_selection"],          self.growSelection_,          "Grow",     "+"),
				(translations["select_between"],          self.fillSelection_,          "Between",  ":"),
				(translations["select_linked_hints"],     self.selectLinkedHints_,      "Corners",  "<"),
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

			if len(self.layer().selection) < 2: return

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

				# check if shortest path is direct from node 1 to node 2
				is_contiguous_shortest = (node2.index - node1.index <= node1.index + len(path.nodes) - node2.index)
				is_contiguous = (not path.closed) or is_contiguous_shortest

				if (is_contiguous):
					# shortest (or only) path is direct from node 1 to node 2
					nodesToSelect.extend(path.nodes[node1.index:node2.index])
				else:
					# shortest path crosses path bounds
					nodesToSelect.extend(path.nodes[0:node1.index])
					nodesToSelect.extend(path.nodes[node2.index:])

				self.selectElements_(nodesToSelect)
		except:
			print(traceback.format_exc())

	# 
	# Selection utils
	# 
	def selectElements_withBooleanOperation_(self, elements, booleanOperation):
		try:
			self.layer().beginChanges()
			
			if (booleanOperation):
				# selecting
				self.layer().selection.extend(elements)
			else:
				# deselecting
				for element in elements:
					self.layer().selection.remove(element)

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

	def selectNodesByType_andSmooth_withOperation_andKey_(self, type, smooth, operation, key):
		try:
			selectionArray = []
			print("key", key)

			# Get nodes on outside edges of selection
			for path in self.layer().paths:
				for node in path.nodes:
					conditions = []
					
					rowSetting = next((item for item in self.rowSettings if item["label"] == key), None)
					typeFilter = rowSetting["options"][rowSetting["option"]] # extremes, all, etc
					if (typeFilter == "Extremes"):
						conditions.append(is_node_extreme(node))
					if (typeFilter == "NonExtremes"):
						conditions.append(not is_node_extreme(node))

					# properties
					end_of_open_path = not path.closed and (node.index == 0 or node.index == len(path.nodes) - 1)
					sharp_line_that_neighbors_offcurve = node.type == LINE and node.smooth is not True and (self.prevNode(node).type == OFFCURVE or self.nextNode(node).type == OFFCURVE)
					smooth_end_of_open_path = end_of_open_path and ((node.smooth and type == CURVE) or node.type == LINE)
					neighboring_offcurve = self.prevNode(node).type == OFFCURVE or self.nextNode(node).type == OFFCURVE
					smooth_line = node.type == LINE and node.smooth is True

					if type:
						# for smooth curves, ignore end of open paths
						if type == CURVE and (smooth is True):
							if end_of_open_path:
								conditions.append(False)
						# for lines ignore those that neighbor offcurves AND are the end of a path
						if type == LINE:
							if end_of_open_path and neighboring_offcurve:
								conditions.append(False)
						# for sharp curves, ignore end of open paths that don't neighbor offcurves
						if type == CURVE and (smooth is False) and end_of_open_path and not neighboring_offcurve:
							conditions.append(False)

						# for sharp curves, include sharp lines that neighbors offcurves
						if type == CURVE and (smooth is False) and sharp_line_that_neighbors_offcurve:
							conditions.append(True)
						# for sharp curves, include smooth ends of open paths
						elif type == CURVE and (smooth is False) and smooth_end_of_open_path:
							conditions.append(True)
						# for smooth curves, include smooth lines
						elif type == CURVE and (smooth is True) and smooth_line:
							conditions.append(True)
						else:
							conditions.append(node.type == type)
							if smooth is not None:
								conditions.append(node.smooth == smooth)

					# if all conditions pass...
					if all(conditions):
						selectionArray.append(node)
						# if looking for LINEs, select neighboring (non-OFFCURVE) node as well
						if type == LINE:
							if node.type == LINE:
								if self.prevNode(node) and self.prevNode(node).type != OFFCURVE:
									selectionArray.append(self.prevNode(node))
							if self.nextNode(node).type != OFFCURVE:
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
		self.selectNodesByType_andSmooth_withOperation_andKey_(CURVE, True, operation, "Smooth")
	def selectSharpCurves_withOperation_(self, sender, operation):
		self.selectNodesByType_andSmooth_withOperation_andKey_(CURVE, False, operation, "Sharp")
	def selectLines_withOperation_(self, sender, operation):
		self.selectNodesByType_andSmooth_withOperation_andKey_(LINE, None, operation, "Lines")
	def selectHandles_withOperation_(self, sender, operation):
		self.selectNodesByType_andSmooth_withOperation_andKey_(OFFCURVE, None, operation, "Handles")
	def selectAnchors_withOperation_(self, sender, operation):
		selectionArray = []
		
		rowSetting = next((item for item in self.rowSettings if item["label"] == "Anchors"), None)
		typeFilter = rowSetting["options"][rowSetting["option"]] # locked, unlocked, etc
		print("typeFilter", typeFilter)
		
		anchors = self.layer().anchors
		for anchor in anchors:
			if typeFilter == "All":
				selectionArray.append(anchor)
			elif typeFilter == "Anchors" and anchor.name[0] != "_":
				selectionArray.append(anchor)
			elif typeFilter == "UnderscoredAnchors" and anchor.name[0] == "_":
				selectionArray.append(anchor)
			elif typeFilter == "Entry" and "entry" in anchor.name.lower():
				selectionArray.append(anchor)
			elif typeFilter == "Exit" and "exit" in anchor.name.lower():
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

			allGuides = []
			globalGuides = Glyphs.font.selectedFontMaster.guides
			localGuides = self.layer().guides
			allGuides.extend(globalGuides)
			allGuides.extend(localGuides)

			rowSetting = next((item for item in self.rowSettings if item["label"] == "Guides"), None)
			typeFilter = rowSetting["options"][rowSetting["option"]] # locked, unlocked, etc

			for guide in allGuides:
				if typeFilter == "All":
					selectionArray.append(guide)
				elif typeFilter == "Locked" and guide.locked:
					selectionArray.append(guide)
				elif typeFilter == "Unlocked" and not guide.locked:
					selectionArray.append(guide)
				elif typeFilter == "Global" and guide in globalGuides:
					selectionArray.append(guide)
				elif typeFilter == "Local" and guide in localGuides:
					selectionArray.append(guide)

			self.performSelectionOnArray_andOperation_(selectionArray, operation)
		except:
			print(traceback.format_exc())

	# 
	# Transfers, Links
	# TODO: make these transfers optional, and allow for removing from selection or adding to selection
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

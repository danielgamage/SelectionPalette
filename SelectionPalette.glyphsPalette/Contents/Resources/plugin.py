# encoding: utf-8

###########################################################################################################
#
#
#	Palette Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Palette
#
#
###########################################################################################################

from __future__ import print_function
from enum import Enum
from importlib.metadata import distribution
import objc
from AppKit import NSMenuItem, NSImage
from GlyphsApp import *
from GlyphsApp import Glyphs, EDIT_MENU, LINE, CURVE, OFFCURVE
from GlyphsApp.plugins import *
from vanilla import Window, Button, ImageButton, Group, TextBox, VerticalStackView, HorizontalStackView, ImageView
import traceback, os

class Operation(Enum):
	ADD = 0
	SUBTRACT = 1
	INTERSECT = 2


class SelectionPalette(PalettePlugin):
		
	def settings(self):
		try:
			# print("SelectionPalette hello0")
			self.buttonList = []
			self.name = "SelectionPalette"
			# Create Vanilla window and group with controls
			width = 180
			height = 200
			types = (
				("SmoothCurves", "Smooth", self.selectSmoothCurves_withOperation_),
				("SharpCurves", "Sharp", self.selectSharpCurves_withOperation_),
				("Lines", "Lines", self.selectLines_withOperation_),
				("Handles", "Handles", self.selectHandles_withOperation_),
				("Corners", "Corners", self.selectComponents_withOperation_),
				("Components", "Components", self.selectComponents_withOperation_),
				("Guides", "Guides", self.selectGuides_withOperation_),
				("Anchors", "Anchors", self.selectAnchors_withOperation_),
				)
			self.paletteView = Window((width, height))
			self.paletteView.group = Group((0, 0, width, height))
			self.paletteView.group.stack = VerticalStackView((0, 0, width, height), views=[], edgeInsets=(4, 8, 8, 8), distribution="equalSpacing", alignment="center")

			addIcon = NSImage.alloc().initWithContentsOfFile_(os.path.join(os.path.dirname(__file__), 'union.svg'))
			addIcon.setTemplate_(True)
			subtractIcon = NSImage.alloc().initWithContentsOfFile_(os.path.join(os.path.dirname(__file__), 'subtract.svg'))
			subtractIcon.setTemplate_(True)
			intersectIcon = NSImage.alloc().initWithContentsOfFile_(os.path.join(os.path.dirname(__file__), 'intersect.svg'))
			intersectIcon.setTemplate_(True)
			
			for type,label,callback in types:
				addButton = ImageButton(
					"auto",
					bordered=False,
					imageObject=addIcon,
					# avoiding late binding of `callback`:
					callback=lambda sender, callback=callback: callback(sender, Operation.ADD)
				)
				subtractButton = ImageButton(
					"auto",
					bordered=False,
					imageObject=subtractIcon,
					callback=lambda sender, callback=callback: callback(sender, Operation.SUBTRACT)
				)
				intersectionButton = ImageButton(
					"auto",
					bordered=False,
					imageObject=intersectIcon,
					callback=lambda sender, callback=callback: callback(sender, Operation.INTERSECT)
				)
				
				# see https://github.com/robotools/vanilla/issues/165
				self.buttonList.extend([addButton, subtractButton, intersectionButton])
				
				osource_image = os.path.join(os.path.dirname(__file__), type + '.svg')
				icon = NSImage.alloc().initWithContentsOfFile_(osource_image)
				icon.setTemplate_(True) # inherit fill color from surrounding text
				imageView = ImageView((0, 0, 32, 32))
				imageView.setImage(imageObject=icon)
				row = HorizontalStackView(
					(0, 0, width, 0), 
					views=[
						dict(view=imageView, width=22),
						dict(view=TextBox("auto", text=label, sizeStyle="small"), width=72),
						dict(view=HorizontalStackView(
							(0, 0, 12, 0),
							views=[
								dict(view=addButton),
								dict(view=subtractButton),
								dict(view=intersectionButton),
							],
							spacing=4,
						)),
					],
					spacing=4,
					distribution="gravity",
					alignment="center",
					edgeInsets=(0, 0, 0, 0),
				)
				 # callback[1](sender, Operation.ADD)
				self.paletteView.group.stack.appendView(row)

			# Set dialog to NSView
			self.dialog = self.paletteView.group.getNSView()
			
			# Edit menu additions
			invertMenuItemIndex = Glyphs.menu[EDIT_MENU].submenu().indexOfItemWithTitle_("Invert Selection") + 1
			menuItems = (
				("Continue Selection", self.continueSelection_),
				("Undo Selection",     self.undoSelection_),
				("Grow Selection",     self.growSelection_),
				("Shrink Selection",   self.shrinkSelection_),
				("Select Between",     self.fillSelection_)
				)
			for menuItem in menuItems:
				item = NSMenuItem(*menuItem)
				Glyphs.menu[EDIT_MENU].submenu().insertItem_atIndex_(item, invertMenuItemIndex)
				invertMenuItemIndex += 1
		except:
			print(traceback.format_exc())

	def layer(self):
		return Glyphs.font.selectedLayers[0]
		
	def continueSelection_(self, sender):
		try:
			#  Need at least two nodes to infer a pattern
			if len(self.layer().selection) >= 2:
				lastNode = self.layer().selection[-1]
				originNode = self.layer().selection[-2]

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
						if node.nextNode.selected or node.prevNode.selected:
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
						if not node.nextNode.selected or not node.prevNode.selected:
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

	# Selection utils
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

	# - (void) selectNodesByType:(GSNodeType)type andSmooth:(GSNodeType)connection withOperation:(SelectionOperationType)operation {
	# 	NSMutableArray *selectionArray = [[NSMutableArray alloc] init];

	# 	for (GSPath *path in [self layer].paths){
	# 		for (GSNode *node in path.nodes) {
	# 			NSMutableArray *conditions = [[NSMutableArray alloc] init];

	# 			// if type is set
	# 			if (type) {
	# 				// when looking for sharp curves, add sharp lines that neighbor offcurves
	# 				if (type == CURVE && node.type == LINE && node.connection == SHARP && ([self nextNode:node].type == OFFCURVE || [self nextNode:node].type == OFFCURVE)) {
	# 					[conditions addObject:[NSNumber numberWithBool:YES]];
	# 				} else {
	# 					[conditions addObject:[NSNumber numberWithBool:(node.type == type)]];
	# 				}
	# 			}
	# 			// if connection is set
	# 			if (connection == SHARP || connection == SMOOTH) {
	# 				[conditions addObject:[NSNumber numberWithBool:(node.connection == connection)]];
	# 			}

	# 			// if all conditions pass...
	# 			if (![conditions containsObject:@(0)]) {
	# 				[selectionArray addObject:node];
	# 				// if looking for lines, select prevNode as well (unless it's OFFCURVE)
	# 				if (type == LINE && node.type == LINE) {
	# 					[selectionArray addObject:[self prevNode:node]];
	# 				}
	# 				// if looking for lines, add next (non-offcurve) node
	# 				if (type == LINE && [self nextNode:node].type != OFFCURVE) {
	# 					[selectionArray addObject:[self nextNode:node]];
	# 				}
	# 			}
	# 		}
	# 	}

	# 	[self performSelectionOnArray:selectionArray andOperation:operation];
	# }
	
	def selectNodesByType_andSmooth_withOperation_(self, type, smooth, operation):
		try:
			selectionArray = []

			# Get nodes on outside edges of selection
			for path in self.layer().paths:
				for node in path.nodes:
					conditions = []
					
					if type:
						# when looking for sharp curves, add sharp lines that neighbor offcurves
						if type == CURVE and node.type == LINE and not node.smooth and (node.nextNode.type == OFFCURVE or node.nextNode.type == OFFCURVE):
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
							if node.prevNode and node.prevNode.type != OFFCURVE:
								selectionArray.append(node.prevNode)
						# if looking for LINEs, add next (non-offcurve) node
						if type == LINE and node.nextNode.type != OFFCURVE:
							selectionArray.append(node.nextNode)
					

			# Select them
			print(operation, selectionArray)
			self.performSelectionOnArray_andOperation_(selectionArray, operation)
		except:
			print(traceback.format_exc())

	# - (void) selectAnchorsWithOperation:(SelectionOperationType)operation {
	#     NSMutableArray *selectionArray = [[NSMutableArray alloc] init];

	#     for (NSString *key in [self layer].anchors) {
	#         GSAnchor *anchor = [[self layer].anchors objectForKey:key];
	#         [selectionArray addObject:anchor];
	#     }

	#     [self performSelectionOnArray:selectionArray andOperation:operation];
	# }

	# - (void) selectComponentsWithOperation:(SelectionOperationType)operation {
	#     NSMutableArray *selectionArray = [[NSMutableArray alloc] init];

	#     for (GSElement *component in [self layer].components) {
	#         [selectionArray addObject:component];
	#     }

	#     [self performSelectionOnArray:selectionArray andOperation:operation];
	# }
	
	def selectGuides_withOperation_(self, sender, operation):
		try:
			selectionArray = []

			globalGuides = Glyphs.font.selectedFontMaster.guides
			localGuides = self.layer().guides
			selectionArray.extend(globalGuides)
			selectionArray.extend(localGuides)

			print(selectionArray)
			self.performSelectionOnArray_andOperation_(selectionArray, operation)
		except:
			print(traceback.format_exc())

	def selectSmoothCurves_withOperation_(self, sender, operation):
		print("selectSmoothCurves")
		# should select both line and curve nodes with smooth connections
		self.selectNodesByType_andSmooth_withOperation_(None, True, operation)
	def selectSharpCurves_withOperation_(self, sender, operation):
		print("selectSharpCurves")
		self.selectNodesByType_andSmooth_withOperation_(CURVE, False, operation)
	def selectLines_withOperation_(self, sender, operation):
		print("selectLines")
		self.selectNodesByType_andSmooth_withOperation_(LINE, None, operation)
	def selectHandles_withOperation_(self, sender, operation):
		print("selectHandles")
		self.selectNodesByType_andSmooth_withOperation_(OFFCURVE, None, operation)
	def selectAnchors_withOperation_(self, sender, operation):
		print("selectAnchors")
		# self.selectNodesByType_andSmooth_withOperation_(operation)
	def selectComponents_withOperation_(self, sender, operation):
		print("selectComponents")
		# self.selectNodesByType_andSmooth_withOperation_(operation)

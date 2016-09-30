//
//  SelectionPalette.m
//  SelectionPalette
//
//  Created by Daniel Gamage on 9/27/16.
//  Copyright © 2016 Daniel Gamage. All rights reserved.
//

#import "SelectionPalette.h"
#import <GlyphsCore/GSFont.h>
#import <GlyphsCore/GSFontMaster.h>
#import <GlyphsCore/GSGlyph.h>
#import <GlyphsCore/GSLayer.h>
#import <GlyphsCore/GSPath.h>
#import <GlyphsCore/GSElement.h>
#import <GlyphsCore/GSNode.h>
#import <GlyphsCore/GSWindowControllerProtocol.h>

@implementation SelectionPalette

@synthesize windowController;

- (id) init {
    self = [super init];
    [NSBundle loadNibNamed:@"SelectionPaletteView" owner:self];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(update:) name:@"GSUpdateInterface" object:nil];
    return self;
}

- (NSUInteger) interfaceVersion {
    // Distinguishes the API verison the plugin was built for. Return 1.
    return 1;
}

- (NSString*) title {
    // Return the name of the tool as it will appear in the menu.
    return @"Selection Palette";
}

- (void)update:(id)sender {
    layer = [windowController activeLayer];
}

- (GSNode*) getSibling:(GSNode*)node next:(bool)next {
    GSPath *path = node.parent;
    NSUInteger index = [path indexOfNode:node];
    NSUInteger length = [path.nodes count];
    NSUInteger siblingIndex;

    if (next == YES) {
        // if last node
        siblingIndex = (index == length - 1) ? 0 : index + 1;
    } else {
        // if first node
        siblingIndex = (index == 0) ? length - 1 : index - 1;
    }

    GSNode *nextNode = [path nodeAtIndex:siblingIndex];
    return nextNode;
}

- (GSNode*) prevNode:(GSNode*)node {
    return [self getSibling:node next:NO];
}

- (GSNode*) nextNode:(GSNode*)node {
    return [self getSibling:node next:YES];
}

- (bool) isSelected:(GSNode*)node {
    return ([layer.selection containsObject:node]);
}

- (void) growSelection {
    NSMutableArray *nodesToSelect = [[NSMutableArray alloc] init];

    // Get nodes on outside edges of selection
    for (GSPath *path in layer.paths) {
        for (GSNode *node in path.nodes) {
            if (![self isSelected:node]) {
                if ([self isSelected:[self nextNode:node]] || [self isSelected:[self prevNode:node]]) {
                    [nodesToSelect addObject:node];
                }
            }
        }
    }
    // Select them
    for (GSNode *node in nodesToSelect) {
        [layer addSelection:node];
    }

}

- (void) shrinkSelection {
    NSMutableArray *nodesToDeselect = [[NSMutableArray alloc] init];

    // Get nodes on inside edges of selection
    for (GSPath *path in layer.paths) {
        for (GSNode *node in path.nodes) {
            if ([self isSelected:node]) {
                if (![self isSelected:[self nextNode:node]] || ![self isSelected:[self prevNode:node]]) {
                    [nodesToDeselect addObject:node];
                }
            }
        }
    }

    // Deselect them
    for (GSNode *node in nodesToDeselect) {
        [layer removeObjectFromSelection:node];
    }
}

- (void) continueSelection {
    if ([layer.selection count] >= 2) {
        GSNode *lastNode = layer.selection[[layer.selection count] - 1];
        GSNode *originNode = layer.selection[[layer.selection count] - 2];
        GSPath *path = originNode.parent;
        NSUInteger lastNodeIndex = [path indexOfNode:lastNode];
        NSUInteger originNodeIndex = [path indexOfNode:originNode];
        NSUInteger rhythm;

        // Get difference of two nodes
        if (lastNodeIndex > originNodeIndex) {
            // normal diff
            rhythm = lastNodeIndex - originNodeIndex;
        } else {
            // crossing bounds of path
            rhythm = abs(originNodeIndex - [path.nodes count]) + lastNodeIndex;
        }

        // Move to node with rhythm
        GSNode *nodeToSelect = lastNode;
        int i = 0;
        while (i < rhythm) {
            nodeToSelect = [self nextNode:nodeToSelect];
            i += 1;
        }

        // Select it
        [layer addSelection:nodeToSelect];
    }
}

- (void) performSelectionWithArray:(NSMutableArray *)selectionArray andOperation:(SelectionOperationType)operation {
    if (operation == ADD) {
        [layer addObjectsFromArrayToSelection:selectionArray];
    } else if (operation == SUBTRACT) {
        [layer removeObjectsFromSelection:selectionArray];
    } else if (operation == INTERSECT) {
        NSMutableArray *elementsToDeselect = [[NSMutableArray alloc] init];
        for (GSElement *element in layer.selection) {
            if (![selectionArray containsObject:element]) {
                [elementsToDeselect addObject:element];
            }
        }
        [layer removeObjectsFromSelection:elementsToDeselect];
    }
}

- (void) selectAnchorwithOperation:(SelectionOperationType)operation {
    NSMutableArray *selectionArray = [[NSMutableArray alloc] init];

    for (NSString *key in layer.anchors) {
        GSAnchor *anchor = [layer.anchors objectForKey:key];
        [selectionArray addObject:anchor];
    }

    [self performSelectionWithArray:selectionArray andOperation:operation];
}

- (void) selectNodeByType:(GSNodeType)type andSmooth:(GSNodeType)connection withOperation:(SelectionOperationType)operation {
    NSMutableArray *selectionArray = [[NSMutableArray alloc] init];

    for (GSPath *path in layer.paths){
        for (GSNode *node in path.nodes) {
            NSMutableArray *conditions = [[NSMutableArray alloc] init];

            // if type is set
            if (type) {
                [conditions addObject:([NSNumber numberWithBool:(node.type == type)])];
            }
            // if connection is set
            if (connection == SMOOTH || connection == SHARP) {
                [conditions addObject:([NSNumber numberWithBool:(node.connection == connection)])];
            }

            // if all conditions pass...
            if (![conditions containsObject:@(0)]) {
                [selectionArray addObject:node];
            }
        }
    }

    [self performSelectionWithArray:selectionArray andOperation:operation];
}

- (void) undoSelection {
    [layer removeObjectFromSelection:[layer.selection lastObject]];
}

- (IBAction) growSelection:(id)sender {
    [self growSelection];
}
- (IBAction) shrinkSelection:(id)sender {
    [self shrinkSelection];
}
- (IBAction) continueSelection:(id)sender {
    [self continueSelection];
}
- (IBAction) undoSelection:(id)sender {
    [self undoSelection];
}
- (IBAction) selectSmoothCurves:(id)sender {
    SelectionOperationType operation = [sender selectedSegment];
    // should select both line and curve nodes with smooth on
//    [self selectNodeByType:LINE andSmooth:SMOOTH withOperation:operation];
    [self selectNodeByType:nil andSmooth:SMOOTH withOperation:operation];
}
- (IBAction) selectSharpCurves:(id)sender {
    SelectionOperationType operation = [sender selectedSegment];
    [self selectNodeByType:CURVE andSmooth:SHARP withOperation:operation];
}
- (IBAction) selectLines:(id)sender {
    SelectionOperationType operation = [sender selectedSegment];
    [self selectNodeByType:LINE andSmooth:SHARP withOperation:operation];
}
- (IBAction) selectHandles:(id)sender {
    SelectionOperationType operation = [sender selectedSegment];
    [self selectNodeByType:OFFCURVE andSmooth:SHARP withOperation:operation];
}
- (IBAction) selectAnchors:(id)sender {
    SelectionOperationType operation = [sender selectedSegment];
    [self selectAnchorwithOperation:operation];
}

- (NSInteger) maxHeight {
    return 265;
}
- (NSInteger) minHeight {
    return 125;
}
- (NSUInteger) currentHeight {
    return [[NSUserDefaults standardUserDefaults] integerForKey:@"SelectionPaletteCurrentHeight"];
}
@end

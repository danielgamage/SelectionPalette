//
//  SelectionPalette.h
//  SelectionPalette
//
//  Created by Daniel Gamage on 9/27/16.
//  Copyright © 2016 Daniel Gamage. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <GlyphsCore/GlyphsPaletteProtocol.h>
#import <GlyphsCore/GSGlyphViewControllerProtocol.h>

@interface SelectionPalette : NSObject <GlyphsPalette> {
    NSView *					__unsafe_unretained _theView;
    IBOutlet NSButton *growButton;
    IBOutlet NSButton *shrinkButton;
    IBOutlet NSButton *continueButton;
    IBOutlet NSButton *undoButton;
    __weak IBOutlet NSSegmentedControl *selectSmoothCurves;
    __weak IBOutlet NSSegmentedControl *selectSharpCurves;
    __weak IBOutlet NSSegmentedControl *selectLines;
    __weak IBOutlet NSSegmentedControl *selectHandles;
    __weak IBOutlet NSSegmentedControl *selectAnchors;
    __weak IBOutlet NSSegmentedControl *selectComponents;
}

@property (assign, nonatomic) IBOutlet NSView *theView;

/**
 An enumeration of selection operation types.
 */
typedef NS_ENUM(uint8_t, SelectionOperationType) {
    ADD = 0,
    SUBTRACT = 1,
    INTERSECT = 2,
};

@end

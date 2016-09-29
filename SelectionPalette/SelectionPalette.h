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
    GSLayer *layer;
    IBOutlet NSButton *growButton;
    IBOutlet NSButton *shrinkButton;
    IBOutlet NSButton *continueButton;
    IBOutlet NSButton *undoButton;
}
@property (assign, nonatomic) IBOutlet NSView *theView;
@end

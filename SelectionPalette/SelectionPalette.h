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
#import <GlyphsCore/GlyphsPathPlugin.h>
#import <GlyphsCore/GSGlyphViewControllerProtocol.h>

@interface SelectionPalette : NSObject <GlyphsPalette> {
	NSView *					__unsafe_unretained _theView;
    GSLayer *layer;
    __weak NSViewController<GSGlyphEditViewControllerProtocol> *_editViewController;
    IBOutlet NSButton *growButton;
}
@property (assign, nonatomic) IBOutlet NSView *theView;
@end

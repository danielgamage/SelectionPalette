//
//  SelectionPalette.h
//  SelectionPalette
//
//  Created by Daniel Gamage on 9/27/16.
//  Copyright © 2016 Daniel Gamage. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <GlyphsCore/GlyphsPaletteProtocol.h>

@interface SelectionPalette : NSObject <GlyphsPalette> {
	NSView *					__unsafe_unretained _theView;

}
@property (assign, nonatomic) IBOutlet NSView *theView;
@end

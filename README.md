# SelectionPalette
adapted from https://github.com/danielgamage/Glyphs-Scripts

![Selection Palette Screenshot](https://github.com/danielgamage/SelectionPalette/blob/master/Images/screenshot.png?raw=true)

## Installation
### Recommended
Download _SelectionPalette_ via the Glyphs [Plugin Manager](https://github.com/schriftgestalt/glyphs-packages). (Window > Plugin Manager)

### Alternative
1. Clone or download this repository
1. (Unzip if necessary) and open the file with the `.glyphsPalette` extension.
1. Follow the "are you sure you want to install" dialogs
1. Restart glyphs

## Usage

### Selection commands
In the Edit menu, you'll see some new commands under the other selection commands:
#### Continue Selection
to select a node based on the pattern of the last two nodes you selected
#### Undo Selection
to remove the last-selected node from the selection set
#### Grow Selection
to add closest siblings of selected nodes to the selection set
#### Shrink Selection
to shrink outer edges of a selection set

These all have corresponding keyboard shortcuts for easy access.

### Select by type
The palette in the sidebar contain selection operations for several types of elements:
- smooth curves
- sharp corners
- lines
- handles
- anchors
- components

Each type allows for three selection operations
- ( `+` ) add elements of type to current selection
- ( `-` ) subtract elements from current selection
- ( `○` ) select only elements of type from current selection

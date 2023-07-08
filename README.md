# SelectionPalette
adapted from https://github.com/danielgamage/Glyphs-Scripts

![Selection Palette Screenshot](https://github.com/danielgamage/SelectionPalette/blob/main/Images/screenshot.png?raw=true)

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
In the Edit menu, you'll see some new commands under the other selection commands that all have corresponding keyboard shortcuts for easy access:
#### Undo Selection (`⌥⌘[`)
Removes the last-selected node from the selection set
#### Continue Selection (`⌥⌘]`)
Selects a node based on the pattern of the last two nodes you selected
#### Grow Selection (`⌥⌘+`)
Adds closest siblings of selected nodes to the selection set
#### Shrink Selection (`⌥⌘-`)
Shrinks outer edges of a selection set
#### Select Between (`⌥⌘:`)
Selects all nodes between two selected nodes (the two most recently selected nodes)
#### Select Linked Hints (`⌥⌘<`)
Corner, cap, and segment components are all linked to a given node. This command transfers selections of nodes to their linked components.

### Select by type
The palette in the sidebar contain selection operations for several types of elements:

- **Smooth curves**
  
  Nodes with even handles

- **Sharp corners**
  
  Nodes with uneven handles

- **Lines**
  
  Nodes bordering lines (path segments without handles)

- **Handles**
  
  Offcurve nodes

- **Anchors**
  
  Anchors for composite glyphs

- **Components**
  
  Includes basic components, but not corners or segments.

- **Guides**
  
  Includes both global and local guides—careful!

Each type allows for three selection operations
- **Add** elements of type to current selection
- **Subtract** elements from current selection
- **Select only** elements of type from current selection

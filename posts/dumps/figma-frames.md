# Figma's Frames, Layers, and Canvas: A Mental Model for PowerPoint/Inkscape Users

*From my "Tiago & AI" series — useful bits from my conversations with AI, lightly edited for a general audience.*

---

If you're a researcher or engineer used to PowerPoint or Inkscape, Figma's mental model is slightly different. This post covers the key concepts — frames, layers, groups, and the canvas — mapped to what you already know.

This came out of a conversation with Claude Opus 4.6 while making a scientific poster in Figma. Lightly edited for a general audience.

## Frames are the core building block

In PowerPoint, you have slides, and each slide contains shapes, text boxes, and images. In Inkscape, you have a canvas with objects stacked on top of each other, and you can group them. Figma combines both ideas.

A frame is like a slide in PowerPoint *and* a group at the same time. Your main design frame is essentially your artboard — it defines the boundaries of your design. But unlike PowerPoint slides, frames can be nested inside other frames. So you could have a frame for a whole poster, containing a frame for the header section, containing a frame for each author's info block. It's frames all the way down.

## The Layers panel is a tree, not a flat list

In Inkscape, you have layers stacked vertically, and objects sit on layers. In Figma, there are no separate "layers" — everything is just a tree of nested elements. The Layers panel on the left shows this tree. Items higher in the list render *on top* of items lower in the list (just like Inkscape's z-order). The expand arrows let you drill into groups and frames to see their children.

## Groups vs Frames

A Group (like in Inkscape/PowerPoint) is just a container that wraps its children — it shrinks and grows to fit them. A Frame is more rigid: it has its own fixed dimensions, can clip content that overflows, and can have its own background fill, layout rules, etc. When in doubt, frames are more powerful.

## Everything lives on one infinite canvas

Unlike PowerPoint where slides are separate pages, all your frames sit on one big zoomable canvas. You might have multiple designs as sibling frames on this canvas — like having multiple Inkscape drawings on one huge sheet. This means other frames can overlap or sit nearby, which can be confusing at first if you're only working on one of them.

## The biggest interaction difference

The closest analogy is that Figma is like Inkscape but with PowerPoint-like ease of use, where "groups that clip their content" (frames) replace both artboards and containers. Double-clicking drills *into* a frame to select its children, rather than selecting the frame itself — this is probably the biggest interaction difference from Inkscape, where you'd use the XML editor or object tree to navigate hierarchy.

## Practical things that tripped me up

**Exporting:** There's no "Save as PDF" like in Inkscape. Instead, you select the frame you want to export, then scroll the right sidebar all the way down — past Fill, Stroke, Effects, etc. — until you find a small "Export" section at the very bottom. It's easy to miss because it's not a prominent button, just another section in that long property list. Click the "+" there to add an export format (PDF, PNG, SVG, etc.) and then hit "Export." The key insight is that you export *individual frames*, not the whole file — so select your poster frame first. For a scientific poster, PDF at 1x is usually what you want.

**Zoom and navigation:** Ctrl+scroll zooms in and out (like Inkscape), but Figma has three Shift+number shortcuts worth memorizing. Shift+1 zooms to fit *everything* on your canvas into view — useful when you're lost. Shift+2 zooms to fit your *current selection* — so select your poster frame and hit Shift+2 to center on it. Shift+0 resets to 100% zoom, which is handy to check actual pixel size. Between these three, you can always find your way back.

**Text editing:** Double-click a text element to edit it (just like PowerPoint). But if you're nested deep inside frames, you might need to double-click several times to drill into the right level first. If you're clicking and nothing happens, you're probably selecting a parent frame — keep double-clicking.

## Bonus: if you can see it but can't click it

If you ever find a shape on your canvas that you can see but can't select or move, check the Layers panel — it's almost certainly **locked**. Look for a small padlock icon next to the element's name. Right-click it and choose "Unlock," and you're back in business.

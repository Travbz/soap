# Product Requirements Document: Customer Guidance Display System

**Version:** 1.0  
**Status:** Draft  
**Date:** January 2026  
**Related:** PRD-MultiProduct.md

---

## Executive Summary

Add visual guidance system to display graphics, videos, and instructions to customers at key points in the transaction flow, improving user experience and reducing confusion.

---

## Problem Statement

**Current:** Text-only terminal output, customers unsure when to swipe card, which button to press, or when transaction is complete.

**Desired:** Visual guidance (images/videos/animations) at each step to guide customers through the transaction process.

---

## Goals & Non-Goals

### Goals
- ✅ Display graphics/videos at specific transaction states
- ✅ Support multiple media types (images, GIFs, MP4)
- ✅ Easy content management (file-based, no code changes)
- ✅ State-driven display (triggered by transaction events)

### Non-Goals
- ❌ Touchscreen interaction (buttons only)
- ❌ Real-time video streaming
- ❌ Audio playback (silent operation)

---

## User Stories

### US-1: Customer Sees Card Prompt
**As a** customer  
**I want to** see a graphic showing how to swipe my card  
**So that** I know what to do first

**Acceptance:** Display shows card swipe animation when machine is idle

---

### US-2: Customer Sees Product Selection Guide
**As a** customer  
**I want to** see which button corresponds to which product  
**So that** I select the correct product

**Acceptance:** Display shows product layout diagram with button positions

---

### US-3: Owner Updates Display Content
**As a** store owner  
**I want to** replace display content by uploading new image files  
**So that** I can update promotions or instructions without technical help

**Acceptance:** Owner can replace files in media folder, content updates on restart

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────┐
│          main.py                        │
│      (State Machine)                    │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      DisplayManager                     │
│   (New Class - src/display.py)          │
├─────────────────────────────────────────┤
│ - show_state(state_name)                │
│ - show_media(media_path)                │
│ - clear()                               │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│     Display Config                      │
│  (config/display_config.json)           │
├─────────────────────────────────────────┤
│ {                                       │
│   "states": {                           │
│     "idle": {                           │
│       "media": "swipe_card.gif",        │
│       "duration": null                  │
│     },                                  │
│     "dispensing": {                     │
│       "media": "hold_button.mp4",       │
│       "duration": null                  │
│     }                                   │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      Media Files                        │
│  (media/ directory)                     │
├─────────────────────────────────────────┤
│ - swipe_card.gif                        │
│ - hold_button.mp4                       │
│ - product_layout.png                    │
│ - transaction_complete.gif              │
└─────────────────────────────────────────┘
```

---

## Transaction States & Media

### State Flow with Display Content

```
┌──────────────────────┐
│  STATE: idle         │
│  DISPLAY:            │
│  - swipe_card.gif    │
│  "Swipe card to      │
│   begin"             │
└──────┬───────────────┘
       │ Card swiped
       ▼
┌──────────────────────┐
│  STATE: authorizing  │
│  DISPLAY:            │
│  - processing.gif    │
│  "Authorizing..."    │
└──────┬───────────────┘
       │ Approved
       ▼
┌──────────────────────┐
│  STATE: ready        │
│  DISPLAY:            │
│  - product_select.png│
│  "Select product"    │
└──────┬───────────────┘
       │ Button pressed
       ▼
┌──────────────────────┐
│  STATE: dispensing   │
│  DISPLAY:            │
│  - hold_button.mp4   │
│  "Hold to dispense"  │
│  + running total     │
└──────┬───────────────┘
       │ Done pressed
       ▼
┌──────────────────────┐
│  STATE: complete     │
│  DISPLAY:            │
│  - thank_you.gif     │
│  "Thank you!"        │
│  + receipt summary   │
└──────┬───────────────┘
       │ Timeout
       ▼
   (back to idle)
```

---

## DisplayManager Class

**Location:** `/Users/travops/soap/ePort/src/display.py`

### Class Design

```python
class DisplayManager:
    """
    Manages display output for customer guidance
    """
    
    def __init__(self, config_path: str, media_dir: str):
        """
        Args:
            config_path: Path to display_config.json
            media_dir: Directory containing media files
        """
        self.config = self._load_config(config_path)
        self.media_dir = media_dir
        self.current_state = None
        self._init_display()
    
    def show_state(self, state_name: str) -> None:
        """
        Display content for a specific transaction state
        
        Args:
            state_name: State name (idle, authorizing, ready, etc.)
        """
    
    def show_media(self, media_filename: str, duration: Optional[int] = None) -> None:
        """
        Display specific media file
        
        Args:
            media_filename: Media file name in media directory
            duration: Auto-hide after N seconds (None = indefinite)
        """
    
    def show_text(self, text: str, overlay: bool = True) -> None:
        """
        Display text (with or without overlay on media)
        
        Args:
            text: Text to display
            overlay: If True, overlay on current media; if False, text only
        """
    
    def clear(self) -> None:
        """Clear display"""
    
    def update_transaction_info(self, items: List[Dict], total: float) -> None:
        """
        Update transaction summary overlay
        
        Args:
            items: List of dispensed items
            total: Running total price
        """
```

---

## Configuration Format

### display_config.json

**Location:** `/Users/travops/soap/ePort/config/display_config.json`

```json
{
  "display": {
    "width": 1920,
    "height": 1080,
    "fullscreen": true,
    "background_color": "#000000"
  },
  "states": {
    "idle": {
      "media": "swipe_card.gif",
      "text": "Swipe or tap card to begin",
      "text_position": "bottom",
      "duration": null,
      "loop": true
    },
    "authorizing": {
      "media": "processing.gif",
      "text": "Authorizing payment...",
      "text_position": "center",
      "duration": null,
      "loop": true
    },
    "declined": {
      "media": "declined.png",
      "text": "Card declined. Please try another card.",
      "text_position": "bottom",
      "duration": 5,
      "loop": false
    },
    "ready": {
      "media": "product_layout.png",
      "text": "Select product and hold button to dispense",
      "text_position": "bottom",
      "duration": null,
      "loop": false
    },
    "dispensing": {
      "media": "hold_button.mp4",
      "text": null,
      "text_position": "top",
      "duration": null,
      "loop": true,
      "overlay_transaction": true
    },
    "complete": {
      "media": "thank_you.gif",
      "text": "Thank you for your purchase!",
      "text_position": "bottom",
      "duration": 5,
      "loop": false
    },
    "error": {
      "media": "error.png",
      "text": "Error occurred. Please contact staff.",
      "text_position": "center",
      "duration": 10,
      "loop": false
    }
  },
  "fonts": {
    "main": {
      "family": "Arial",
      "size": 48,
      "color": "#FFFFFF",
      "bold": true
    },
    "transaction": {
      "family": "Courier",
      "size": 36,
      "color": "#00FF00"
    }
  }
}
```

---

## Display Technology Options

### Option 1: HDMI Display + pygame (Recommended)
**Pros:**
- Native Python library
- Good for Raspberry Pi
- Handles images, GIFs, video
- Fullscreen support

**Cons:**
- Requires display hardware
- Video playback can be resource-intensive

**Dependencies:** `pygame`, `opencv-python` (for video)

---

### Option 2: HDMI Display + PyQt5
**Pros:**
- Professional UI framework
- Excellent video support
- Smooth animations

**Cons:**
- Heavier dependency
- More complex setup

**Dependencies:** `PyQt5`, `python-vlc`

---

### Option 3: Web-based Display
**Pros:**
- Easy content updates
- Use HTML5/CSS for layout
- Browser handles all media types

**Cons:**
- Requires browser process
- More complex architecture

**Dependencies:** `flask`, Chromium browser

---

**Recommendation:** **Option 1 (pygame)** - Best balance for Raspberry Pi

---

## Media File Structure

```
/Users/travops/soap/ePort/
├── media/
│   ├── idle/
│   │   ├── swipe_card.gif           # Card swipe animation
│   │   └── swipe_card_alt.mp4       # Alternative animation
│   ├── authorizing/
│   │   └── processing.gif           # Loading spinner
│   ├── ready/
│   │   ├── product_layout.png       # Product button diagram
│   │   └── instructions.mp4         # Video instructions
│   ├── dispensing/
│   │   ├── hold_button.mp4          # Hand holding button
│   │   └── pour_animation.gif       # Product pouring
│   ├── complete/
│   │   ├── thank_you.gif            # Thank you animation
│   │   └── receipt.png              # Receipt display
│   └── error/
│       ├── declined.png             # Card declined graphic
│       └── error.png                # Generic error
└── config/
    └── display_config.json          # Display configuration
```

---

## Integration with main.py

### State Transitions with Display Updates

```python
# main.py modifications

from .src.display import DisplayManager
from .config import DISPLAY_CONFIG_PATH, MEDIA_DIR

def main():
    # ... existing setup ...
    
    # Initialize display manager
    display = DisplayManager(
        config_path=DISPLAY_CONFIG_PATH,
        media_dir=MEDIA_DIR
    )
    
    # Main loop
    while True:
        # Idle state
        display.show_state("idle")
        
        status = safe_status_check(payment)
        
        if status == b'6':  # Disabled
            # Request authorization
            display.show_state("authorizing")
            safe_authorization_request(payment, AUTH_AMOUNT_CENTS)
            
            # Check result
            auth_status = safe_status_check(payment)
            
            if auth_status == b'9':  # Approved
                display.show_state("ready")
            elif auth_status.startswith(b'3'):  # Declined
                display.show_state("declined")
                time.sleep(5)  # Show for 5 seconds
        
        elif status == b'9':  # Authorized
            # Customer can dispense
            display.show_state("dispensing")
            
            try:
                handle_dispensing(machine, payment, display)
            except Exception as e:
                display.show_state("error")
                logger.error(f"Error: {e}")
        
        time.sleep(STATUS_POLL_INTERVAL)

def handle_dispensing(machine, payment, display):
    """Modified to update display with transaction info"""
    
    transaction = TransactionTracker()
    
    # ... dispensing logic ...
    
    def on_flowmeter_pulse(ounces, price):
        # Update display with running total
        items = transaction.get_items()
        total = transaction.get_total()
        display.update_transaction_info(items, total)
    
    def on_done_button():
        # Transaction complete
        display.show_state("complete")
        display.show_text(transaction.get_summary(), overlay=True)
        
        # ... send transaction result ...
        
        time.sleep(5)  # Show summary for 5 seconds
```

---

## Configuration in config/__init__.py

```python
# Display configuration
DISPLAY_CONFIG_PATH = '/Users/travops/soap/ePort/config/display_config.json'
MEDIA_DIR = '/Users/travops/soap/ePort/media'
DISPLAY_ENABLED = True  # Set to False to disable display (testing)
DISPLAY_TIMEOUT = 30  # Return to idle after N seconds of inactivity
```

---

## Implementation Phases

### Phase 1: Core Display Manager (Week 1)
- [ ] Create DisplayManager class
- [ ] Implement pygame-based renderer
- [ ] Add config file loading
- [ ] Support static images

### Phase 2: Media Support (Week 2)
- [ ] Add GIF animation support
- [ ] Add MP4 video playback
- [ ] Implement text overlay
- [ ] Add transaction info overlay

### Phase 3: State Integration (Week 3)
- [ ] Integrate with main.py state machine
- [ ] Add display updates at each state transition
- [ ] Test all state flows with media

### Phase 4: Content & Polish (Week 4)
- [ ] Create/commission media files for each state
- [ ] Optimize display performance on Pi
- [ ] Add graceful fallback (no display = text only)
- [ ] Documentation for content updates

---

## Media Content Requirements

### Specifications

| State | Type | Resolution | Duration | File Size |
|-------|------|------------|----------|-----------|
| idle | GIF/MP4 | 1920x1080 | 5-10s loop | < 5MB |
| authorizing | GIF | 1920x1080 | 2-5s loop | < 2MB |
| ready | PNG | 1920x1080 | Static | < 1MB |
| dispensing | MP4 | 1920x1080 | 5-10s loop | < 10MB |
| complete | GIF | 1920x1080 | 3-5s | < 3MB |
| error | PNG | 1920x1080 | Static | < 1MB |

### Design Guidelines
- **High contrast** - Visible in bright/dim environments
- **Clear text** - Minimum 36pt font
- **Simple animations** - Easy to understand at a glance
- **Brand consistent** - Match store branding colors
- **Optimized size** - Fast loading on Raspberry Pi

---

## Edge Cases & Error Handling

### Missing Media File
**Behavior:** Fall back to text-only display, log warning

### Video Playback Failure
**Behavior:** Show static image, continue transaction

### Display Hardware Disconnected
**Behavior:** Continue operation with terminal output only

### Invalid Config Format
**Behavior:** Use default hardcoded state config, log error

---

## Testing Strategy

### Unit Tests
- DisplayManager initialization
- Config file parsing and validation
- Media file loading
- State transitions

### Integration Tests
- Display updates during transaction flow
- Text overlay rendering
- Transaction info updates
- Graceful degradation (no display hardware)

### Hardware Tests
- All media types render correctly
- Video loops smoothly
- Text is legible on physical display
- Performance on Raspberry Pi

---

## Performance Considerations

### Raspberry Pi Optimization
- **Pre-load media** - Load all media files at startup
- **Limit video resolution** - 1080p max, consider 720p
- **Compress videos** - Use H.264 codec, moderate bitrate
- **GIF optimization** - Reduce colors, optimize frames
- **Cache rendered text** - Don't re-render same text

### Memory Management
- Max 100MB total media files
- Unload unused media after timeout
- Monitor GPU memory usage

---

## Migration Strategy

### Backward Compatibility
Display is **optional** - system works without display hardware:
- If DISPLAY_ENABLED = False → terminal output only
- If display hardware not found → fall back to terminal
- All display calls wrapped in try/except

### Deployment
1. Install display hardware (HDMI monitor)
2. Install pygame: `pip install pygame opencv-python`
3. Add media files to `/Users/travops/soap/ePort/media/`
4. Add display_config.json to config/
5. Set DISPLAY_ENABLED = True
6. Restart service

---

## Success Metrics

### Functional
- ✅ Display shows correct content for each state
- ✅ Videos/GIFs loop smoothly
- ✅ Transaction info updates in real-time
- ✅ Graceful fallback to terminal if display fails

### Performance
- ⏱️ State transition < 0.5 seconds
- ⏱️ Video playback > 24 FPS
- 💾 Memory usage < 150MB

### User Experience
- 📊 Customer confusion reduced (measure support calls)
- 📊 Faster transaction times
- 📊 Fewer abandoned transactions

---

## Future Enhancements

- [ ] Multi-language support (swap media per language)
- [ ] Promotional video during idle
- [ ] QR code display for app download
- [ ] Real-time product availability display
- [ ] Touch screen support (future hardware)

---

## Dependencies

### Required
```txt
pygame>=2.1.0         # Display rendering
opencv-python>=4.5.0  # Video playback
Pillow>=9.0.0         # Image processing
```

### Optional
```txt
python-vlc>=3.0.0     # Alternative video player
PyQt5>=5.15.0         # Alternative display framework
```

---

## Example Usage

### Simple State Display
```python
display = DisplayManager(
    config_path="/path/to/display_config.json",
    media_dir="/path/to/media/"
)

# Show idle state
display.show_state("idle")

# Show authorizing with text
display.show_state("authorizing")

# Show product selection
display.show_state("ready")
```

### With Transaction Info
```python
# During dispensing
transaction_items = [
    {"name": "Hand Soap", "quantity": 2.5, "unit": "oz", "price": 0.38}
]
display.update_transaction_info(transaction_items, total=0.38)

# Transaction complete
display.show_state("complete")
display.show_text("Total: $0.38\nThank you!", overlay=True)
```

---

**Document Status:** Ready for Review  
**Dependencies:** None (standalone system)  
**Next Steps:** Review → Approve → Begin Phase 1

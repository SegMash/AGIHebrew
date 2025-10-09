#!/usr/bin/env python3
"""
Send parser commands to a ScummVM (King's Quest III) window using Python.

More reliable than PowerShell SendKeys, especially for Hebrew text and special keys.
"""

import argparse
import time
import sys
from pathlib import Path
from pynput.keyboard import Key, Controller

keyboard = Controller()
try:
    import pyautogui
    import psutil
    import pygetwindow as gw
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install pyautogui psutil pygetwindow")
    sys.exit(1)

# Configure pyautogui
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.1      # Default pause between actions

def find_window_by_title(title_fragment):
    """Find windows containing the title fragment (case-insensitive)."""
    windows = []
    try:
        all_windows = gw.getAllWindows()
        for window in all_windows:
            if window.title and title_fragment.lower() in window.title.lower():
                windows.append(window)
    except Exception as e:
        print(f"Error finding windows: {e}")
    return windows

def activate_window(window):
    """Bring window to foreground and ensure it's active."""
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.2)  # Wait for activation
        return True
    except Exception as e:
        print(f"Error activating window: {e}")
        return False

def is_hebrew_char(char):
    """Check if character is Hebrew."""
    return 0x0590 <= ord(char) <= 0x05FF

def send_char_safe(char, debug=False):
    """Send a character using the most appropriate method."""
    try:
        if is_hebrew_char(char):
            # Use pynput for Hebrew characters (more reliable)
            if debug:
                print(f"  [DEBUG] Sending Hebrew char '{char}' via pynput")
            keyboard.type(char)
            return True
        else:
            # Use pyautogui for ASCII characters
            if debug:
                print(f"  [DEBUG] Sending ASCII char '{char}' via pyautogui")
            pyautogui.write(char)
            return True
    except Exception as e:
        if debug:
            print(f"  [ERROR] Failed to send char '{char}': {e}")
        return False

def send_command(cmd, key_delay=0.05, post_delay=0.3, debug=False):
    """
    Send a command string with support for special keys and Hebrew text.
    
    Special key format: {ENTER}, {F5}, {ESC}, etc.
    """
    if debug:
        print(f"  [DEBUG] Processing command: '{cmd}'")
    
    i = 0
    while i < len(cmd):
        if cmd[i] == '{':
            # Look for closing brace
            close_idx = cmd.find('}', i)
            if close_idx > i:
                # Found special key sequence
                special_key = cmd[i+1:close_idx].upper()
                if debug:
                    print(f"  [DEBUG] Sending special key: {special_key}")
                
                # Handle special keys with pynput for better compatibility
                if special_key in ['ENTER', 'RETURN']:
                    try:
                        keyboard.press(Key.enter)
                        keyboard.release(Key.enter)
                        if debug:
                            print(f"  [DEBUG] ENTER sent via pynput")
                    except Exception as e:
                        print(f"  [ERROR] Failed to send ENTER: {e}")
                elif special_key == 'ESC' or special_key == 'ESCAPE':
                    try:
                        keyboard.press(Key.esc)
                        keyboard.release(Key.esc)
                        if debug:
                            print(f"  [DEBUG] ESC sent via pynput")
                    except Exception as e:
                        print(f"  [ERROR] Failed to send ESC: {e}")
                elif special_key == 'TAB':
                    try:
                        keyboard.press(Key.tab)
                        keyboard.release(Key.tab)
                        if debug:
                            print(f"  [DEBUG] TAB sent via pynput")
                    except Exception as e:
                        print(f"  [ERROR] Failed to send TAB: {e}")
                elif special_key == 'SPACE':
                    try:
                        keyboard.press(Key.space)
                        keyboard.release(Key.space)
                        if debug:
                            print(f"  [DEBUG] SPACE sent via pynput")
                    except Exception as e:
                        print(f"  [ERROR] Failed to send SPACE: {e}")
                else:
                    # Fall back to pyautogui for other special keys
                    key_map = {
                        'BACKSPACE': 'backspace',
                        'DELETE': 'delete',
                        'HOME': 'home',
                        'END': 'end',
                        'PGUP': 'pageup',
                        'PGDN': 'pagedown',
                        'UP': 'up',
                        'DOWN': 'down',
                        'LEFT': 'left',
                        'RIGHT': 'right',
                        'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
                        'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
                        'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12'
                    }
                    
                    if special_key in key_map:
                        try:
                            pyautogui.press(key_map[special_key])
                            if debug:
                                print(f"  [DEBUG] Special key '{special_key}' sent via pyautogui")
                        except Exception as e:
                            print(f"  [ERROR] Failed to send special key '{special_key}': {e}")
                    else:
                        print(f"  [WARNING] Unknown special key: {special_key}")
                
                i = close_idx + 1
                time.sleep(key_delay)
            else:
                # No closing brace, treat as literal
                send_char_safe(cmd[i], debug)
                i += 1
                time.sleep(key_delay)
        else:
            # Regular character - use appropriate method based on character type
            send_char_safe(cmd[i], debug)
            i += 1
            time.sleep(key_delay / 10)  # Faster for regular chars
    
    # Add automatic ENTER if command doesn't end with a special key
    if not cmd.rstrip().endswith('}'):
        if debug:
            print("  [DEBUG] Sending automatic ENTER")
        try:
            #pyautogui.press('enter')
            print("Sending 'Enter' key...")
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            print("Keystroke sent successfully.")
            if debug:
                print("  [DEBUG] Automatic ENTER sent successfully")
        except Exception as e:
            print(f"  [ERROR] Failed to send automatic ENTER: {e}")
    
    time.sleep(post_delay)

def main():
    parser = argparse.ArgumentParser(
        description="Send commands to ScummVM/KQ3 window using Python",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-w', '--window-title', default="King's Quest III",
                       help='Window title fragment to search for')
    parser.add_argument('-c', '--commands', nargs='+',
                       help='Commands to send (can specify multiple)')
    parser.add_argument('-f', '--file', 
                       help='Read commands from file (one per line)')
    parser.add_argument('-s', '--start', type=int, default=1,
                       help='Start from line number when reading from file (1-based)')
    parser.add_argument('--key-delay', type=float, default=0.15,
                       help='Delay between keystrokes (seconds)')
    parser.add_argument('--command-delay', type=float, default=0.3,
                       help='Delay after each command (seconds)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be sent without sending')
    parser.add_argument('--debug', action='store_true',
                       help='Show detailed debug output')
    parser.add_argument('--list-windows', action='store_true',
                       help='List all visible windows and exit')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.start != 1 and not args.file:
        print("Error: --start can only be used with --file")
        return
    
    if args.list_windows:
        print("All visible windows:")
        for window in gw.getAllWindows():
            if window.title.strip():
                print(f"  '{window.title}'")
        return
    
    # Get commands
    commands = []
    file_start_line = 1
    
    if args.commands:
        commands.extend(args.commands)
    
    if args.file:
        # Validate start line
        if args.start < 1:
            print(f"Error: --start must be 1 or greater (got {args.start})")
            return
        
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                all_lines = [line.strip() for line in f]
                non_empty_lines = [line for line in all_lines if line.strip()]
                
                # Show file info
                print(f"File: {args.file}")
                print(f"Total lines: {len(all_lines)}")
                print(f"Non-empty lines: {len(non_empty_lines)}")
                
                if args.start > len(non_empty_lines):
                    print(f"Error: --start {args.start} is beyond file length ({len(non_empty_lines)} non-empty lines)")
                    return
                
                # Extract commands starting from specified line (1-based)
                file_commands = non_empty_lines[args.start-1:]
                file_start_line = args.start
                
                print(f"Starting from line {args.start}, will process {len(file_commands)} command(s)")
                
                commands.extend(file_commands)
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            return
    
    if not commands:
        print("No commands provided. Use -c or -f option.")
        return
    
    # Find target window
    windows = find_window_by_title(args.window_title)
    if not windows:
        print(f"No window found containing title: '{args.window_title}'")
        print("Use --list-windows to see all available windows")
        return
    
    if len(windows) > 1:
        print(f"Multiple windows found ({len(windows)}), using first one:")
        for i, win in enumerate(windows):
            print(f"  {i+1}. '{win.title}'")
    
    target_window = windows[0]
    print(f"Target window: '{target_window.title}'")
    
    if args.dry_run:
        print(f"DRY RUN - Would send {len(commands)} command(s):")
        start_num = file_start_line if args.file else 1
        for i, cmd in enumerate(commands):
            line_num = start_num + i
            print(f"  {line_num:03d}: {cmd}")
        return
    
    # Activate window
    if not activate_window(target_window):
        print("Failed to activate target window")
        return
    
    print(f"Sending {len(commands)} command(s)...")
    print("Move mouse to top-left corner to abort")
    
    # Send commands
    start_num = file_start_line if args.file else 1
    for i, cmd in enumerate(commands):
        line_num = start_num + i
        print(f"{line_num:03d}: {cmd}")
        
        # Re-activate window before each command (in case focus was lost)
        activate_window(target_window)
        
        try:
            send_command(cmd, args.key_delay, args.command_delay, args.debug)
        except pyautogui.FailSafeException:
            print("Aborted by moving mouse to corner")
            break
        except Exception as e:
            print(f"Error sending command: {e}")
            break
    
    print("Done.")

if __name__ == '__main__':
    main()
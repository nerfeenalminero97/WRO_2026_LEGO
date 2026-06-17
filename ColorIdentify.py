from pybricks.hubs import PrimeHub
from pybricks.pupdevices import ColorSensor
from pybricks.parameters import Port
from pybricks.tools import wait

# Initialize hardware
hub = PrimeHub()
sensor = ColorSensor(Port.B)

def get_custom_color_value():
    # Get the HSV data
    h, s, v = sensor.hsv()
    
    # --- 1. THE NEUTRAL CHECK (Priority) ---
    # If Saturation is low (s < 25), it's Black, Gray, or White.
    # We ignore Hue (h) entirely for these.
    
    if s < 25: 
        if v < 20:          # Lowered threshold to catch stubborn Blacks
            return "Black", 0
        elif v > 70:        # High brightness
            return "White", 300
        else:               # Anything in between with low saturation
            return "Black", 150

    # --- 2. THE SPECTRUM CHECK ---
    # We only get here if Saturation (s) is high (meaning it's a "real" color)

    # Red
    if h < 20 or h > 340:
        return "Red", 25
    
    # Yellow
    elif 40 <= h <= 85:
        return "Yellow", 80
        
    # Green (Widened to catch more variants)
    elif 90 <= h <= 180:
        return "Green", 130
        
    # Blue (Only if it's actually saturated/vibrant blue)
    elif 190 <= h <= 270:
        return "Blue", 230
    
    return "Unknown", h

# Main Loop
while True:
    name, val = get_custom_color_value()
    
    # Printing Hue (h), Saturation (s), and Value (v) helps you debug!
    h, s, v = sensor.hsv()
    print("Name: {} | HSV: ({}, {}, {})".format(name, h, s, v))
    
    # Visual feedback on the Hub
    if name == "White": hub.display.char("W")
    elif name == "Black": hub.display.char("B")
    elif name == "Gray": hub.display.char("G")
    else: hub.display.char(name[0])
    
    wait(500) # 1 second delay
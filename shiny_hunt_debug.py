import nuxbt
import numpy as np
import time
import requests
import cv2
import json

# ==========================
# DISCORD
# ==========================

WEBHOOK_URL = "https://discord.com/api/webhooks/1478715653232787466/J-sH7gsZRKZA9PZC4xXavbRW3VZ6Z41M4anryCrIoKeQp_SflQ50h1V4I94OT-GxUH8Z"

dashboard_message_id = None


def create_dashboard():

    global dashboard_message_id

    data = {
        "content": "🎮 **Shiny Hunter Starting...**"
    }

    r = requests.post(WEBHOOK_URL + "?wait=true", json=data)

    dashboard_message_id = r.json()["id"]


def update_dashboard(msg, frame):

    try:

        preview = frame.copy()

        cv2.circle(preview,(PIXEL_X,PIXEL_Y),6,(0,0,255),-1)

        _, buffer = cv2.imencode(".png", preview)

        files = {
            "file": ("screen.png", buffer.tobytes(), "image/png")
        }

        payload = {
            "content": msg,
            "attachments": []  # clears old image so we don't hit the 10 attachment limit
        }

        requests.patch(
            f"{WEBHOOK_URL}/messages/{dashboard_message_id}",
            data={"payload_json": json.dumps(payload)},
            files=files
        )

    except Exception as e:

        log(f"Discord error: {e}")


# ==========================
# VIDEO SETTINGS
# ==========================

WIDTH = 1920
HEIGHT = 1080

PIXEL_X = 659
PIXEL_Y = 367

SHINY_GREEN_THRESHOLD = 170


# ==========================
# TIMER
# ==========================

program_start = time.time()

def log(msg):

    elapsed = time.time() - program_start

    print(f"[{elapsed:8.2f}s] {msg}")


# ==========================
# VIDEO CAPTURE
# ==========================

log("Opening capture card...")

cap = cv2.VideoCapture(2, cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FRAME_WIDTH,1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,1080)

time.sleep(2)

if not cap.isOpened():

    log("Capture card failed to open")
    exit()

latest_frame = None


def update_preview():

    global latest_frame

    ret, frame = cap.read()

    if not ret:
        return

    latest_frame = frame

    preview = frame.copy()

    cv2.circle(preview,(PIXEL_X,PIXEL_Y),6,(0,0,255),-1)

    cv2.imshow("Shiny Hunter Capture", preview)

    cv2.waitKey(1)


def wait_with_preview(seconds):

    end = time.time() + seconds

    while time.time() < end:

        update_preview()

        time.sleep(0.01)


# ==========================
# START NUXBT
# ==========================

log("Starting NUXBT...")

nx = nuxbt.Nuxbt()

controller = nx.create_controller(nuxbt.PRO_CONTROLLER)

log("Waiting for Switch connection...")

nx.wait_for_connection(controller)

log("Controller connected!")

# ==========================
# BUTTON FUNCTIONS
# ==========================

def press(button, duration=0.5):

    log(f"Pressing {button} for {duration}s")

    nx.press_buttons(
        controller,
        [button],
        down=duration
    )

    # small buffer to prevent bluetooth packet overlap
    time.sleep(0.05)


def press_combo(buttons, duration=0.5):

    log(f"Pressing combo {buttons} for {duration}s")

    nx.press_buttons(
        controller,
        buttons,
        down=duration
    )

    time.sleep(0.05)

# ==========================
# RESET SEQUENCE
# ==========================

def run_sequence():

    log("Starting reset sequence")

    press_combo([
    	nuxbt.Buttons.A,
    	nuxbt.Buttons.B,
    	nuxbt.Buttons.X,
    	nuxbt.Buttons.Y
	], 0.4)

    wait_with_preview(5)

    press(nuxbt.Buttons.A)
    wait_with_preview(1)

    press(nuxbt.Buttons.B)
    wait_with_preview(2)

    press(nuxbt.Buttons.A)
    wait_with_preview(5)

    press(nuxbt.Buttons.A)
    wait_with_preview(4)

    press(nuxbt.Buttons.B)
    wait_with_preview(4)

    press(nuxbt.Buttons.A)
    wait_with_preview(2)

    press(nuxbt.Buttons.A)
    wait_with_preview(2)

    press(nuxbt.Buttons.A)
    wait_with_preview(2)

    press(nuxbt.Buttons.A)
    wait_with_preview(6)

    press(nuxbt.Buttons.B)
    wait_with_preview(4)

    press(nuxbt.Buttons.A)
    wait_with_preview(5)

    press(nuxbt.Buttons.X)
    wait_with_preview(1)

    press(nuxbt.Buttons.A)
    wait_with_preview(2)

    press(nuxbt.Buttons.A)
    wait_with_preview(1)

    press(nuxbt.Buttons.A)

    log("Waiting for summary screen...")
    wait_with_preview(3)

    log("Reset sequence complete")


# ==========================
# SAVE SEQUENCE
# ==========================

def save_and_close():

    log("Saving shiny")

    press(nuxbt.Buttons.B)
    wait_with_preview(5)

    press(nuxbt.Buttons.B)
    wait_with_preview(5)

    press(nuxbt.Buttons.B)
    wait_with_preview(5)

    press(nuxbt.Buttons.DPAD_DOWN)
    wait_with_preview(3)

    press(nuxbt.Buttons.DPAD_DOWN)
    wait_with_preview(3)

    press(nuxbt.Buttons.DPAD_DOWN)
    wait_with_preview(3)

    press(nuxbt.Buttons.A)
    wait_with_preview(3)

    press(nuxbt.Buttons.A)
    wait_with_preview(5)

    press(nuxbt.Buttons.A)

    wait_with_preview(10)

    press(nuxbt.Buttons.HOME, 0.2)
    wait_with_preview(5)

    press(nuxbt.Buttons.X)
    wait_with_preview(1)

    press(nuxbt.Buttons.A)


# ==========================
# TRACKING
# ==========================

reset_count = 0
start_time = time.time()

goof_count = 0
goof_times = []

log("Shiny hunter started.")

time.sleep(15)
create_dashboard()


def shiny_probability(attempts):

    odds = 8192

    probability = 1 - ((odds - 1) / odds) ** attempts

    return probability * 100
    
def expected_resets_remaining(attempts):

    odds = 8192

    remaining = odds - attempts

    if remaining < 0:
        remaining = 0

    return remaining


# ==========================
# MAIN LOOP
# ==========================

while True:

    run_sequence()

    frame = latest_frame

    if frame is None:
        continue

    b,g,r = frame[PIXEL_Y,PIXEL_X]

    elapsed = time.time() - start_time

    prob = shiny_probability(reset_count)
    
    remaining = expected_resets_remaining(reset_count)

    log(f"Attempt {reset_count}")
    log(f"Charmander pixel RGB: {r} {g} {b}")

    # ==========================
    # DESYNC BUG CHECK
    # ==========================

    if (r, g, b) in [(255,255,255), (115,255,255)]: 

        goof_count += 1
        goof_times.append(round(elapsed/60,2))

        log("⚠ Program goof detected")

        update_dashboard(
            f"🎮 **Shiny Hunter Running**\n\n"
            f"Attempts: {reset_count}\n"
            f"Pixel RGB: {r},{g},{b}\n"
            f"Time: {round(elapsed/60,2)} minutes\n\n"
            f"📊Chance of shiny by now: {prob:.2f}%\n"
            f"🤓☝️Expected resets remaining: {remaining}\n\n"
            f"Program goofed: {goof_count} times\n"
            f"Times: {goof_times}",
            frame
        )

        reset_count += 1
        continue


    # ==========================
    # NORMAL DASHBOARD UPDATE
    # ==========================

    update_dashboard(
        f"🎮 **Shiny Hunter Running**\n\n"
        f"Attempts: {reset_count}\n"
        f"Pixel RGB: {r},{g},{b}\n"
        f"Time: {round(elapsed/60,2)} minutes\n\n"
        f"📊 Chance of shiny by now: {prob:.2f}%\n\n"
        f"⚠ Program goofed: {goof_count} times\n"
        f"Times: {goof_times}",
        frame
    )


    # ==========================
    # SHINY CHECK
    # ==========================

    if g >= SHINY_GREEN_THRESHOLD:

        log("✨ SHINY FOUND ✨")

        update_dashboard(
            f"✨ **SHINY FOUND!** ✨\n\n"
            f"Resets: {reset_count}\n"
            f"Time: {round(elapsed/60,2)} minutes\n\n"
            f"📊 Chance of shiny by now: {prob:.2f}%\n\n"
            f"⚠ Program goofed: {goof_count} times\n"
            f"Time: {round(elapsed/60,2)} minutes\n"
            f"Chance by now: {prob:.2f}%",
            frame
        )

        press(nuxbt.Buttons.CAPTURE,1.3)

        save_and_close()

        break

    else:

        log("Not shiny")

        reset_count += 1

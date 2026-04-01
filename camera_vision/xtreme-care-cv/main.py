# main.py — XtremeCare full CV+AI pipeline
# Compatible with Python 3.14, ultralytics >= 8.3, mediapipe >= 0.10.18
#
# Controls:
#   SPACE  →  simulate dose dispense event
#   Q      →  quit

import cv2
import time
from datetime import datetime

from config import (
    WEBCAM_INDEX, FRAME_WIDTH, FRAME_HEIGHT,
    PATIENT_ID,
)
from database    import init_db, log_dose, log_verification
from api_client  import post_verification_result, post_dose_event
from recognize   import detect_patient
from verify      import VerificationSession
from utils       import get_session_from_time, get_timestamp, draw_status_overlay

# ── Colour palette (BGR) ────────────────────────────────────────────────────
GREEN  = (0, 220, 0)
RED    = (0, 0, 220)
ORANGE = (0, 165, 255)
WHITE  = (255, 255, 255)
GREY   = (160, 160, 160)


def draw_hud(frame: cv2.typing.MatLike,
             session_name: str,
             face_ok: bool,
             active_session: "VerificationSession | None",
             last_status: "str | None") -> None:
    """Render persistent HUD elements every frame."""
    h, w = frame.shape[:2]

    # Top-left: clock + session
    now_str = datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, f"{now_str}  |  {session_name}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2, cv2.LINE_AA)

    # Top-right: face detection status dot
    dot_color = GREEN if face_ok else RED
    dot_label = "Face: OK" if face_ok else "Face: --"
    cv2.circle(frame, (w - 20, 18), 8, dot_color, -1)
    cv2.putText(frame, dot_label,
                (w - 115, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                dot_color, 2, cv2.LINE_AA)

    # Bottom: verification overlay
    if active_session is not None:
        s = active_session.status
        if s == VerificationSession.STATUS_PENDING:
            draw_status_overlay(frame,
                                "Verifying — move hand to mouth...", ORANGE)
        elif s == VerificationSession.STATUS_VERIFIED:
            draw_status_overlay(frame, "VERIFIED — Intake confirmed!", GREEN)
        else:
            draw_status_overlay(frame, "MISSED — Intake not detected", RED)
    elif last_status == VerificationSession.STATUS_VERIFIED:
        draw_status_overlay(frame, "VERIFIED — Session complete", GREEN)
    elif last_status == VerificationSession.STATUS_MISSED:
        draw_status_overlay(frame, "MISSED — Session complete", RED)
    else:
        cv2.putText(frame, "Press SPACE to simulate dose dispense",
                    (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, GREY, 1, cv2.LINE_AA)


def finalise_session(session: VerificationSession,
                     dispensed_at: str,
                     session_name: str,
                     face_confirmed: bool,
                     hand_detected: bool) -> None:
    """Write results to SQLite and POST to API."""
    verified_at  = get_timestamp()
    status       = session.status

    dispensed_dt  = datetime.fromisoformat(dispensed_at)
    verified_dt   = datetime.fromisoformat(verified_at)
    delay_seconds = int((verified_dt - dispensed_dt).total_seconds())

    # Always write to SQLite first
    dose_row = log_dose(
        patient_id    = PATIENT_ID,
        session       = session_name,
        status        = status,
        dispensed_at  = dispensed_at,
        verified_at   = verified_at,
        delay_seconds = delay_seconds,
    )
    log_verification(
        patient_id    = PATIENT_ID,
        session       = session_name,
        verified      = (status == VerificationSession.STATUS_VERIFIED),
        face_confirmed = face_confirmed,
        hand_detected  = hand_detected,
    )
    print(f"[MAIN] DB logged — dose_id={dose_row.get('id')}  status={status}  "
          f"delay={delay_seconds}s")

    # Best-effort API posts
    post_dose_event(PATIENT_ID, session_name, dispensed_at)
    post_verification_result(
        patient_id    = PATIENT_ID,
        session       = session_name,
        status        = status,
        timestamp     = verified_at,
        delay_seconds = delay_seconds,
    )


def main() -> None:
    init_db()

    cap = cv2.VideoCapture(WEBCAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open webcam at index {WEBCAM_INDEX}.")
        print("        Change WEBCAM_INDEX in config.py if needed.")
        return

    print("=" * 57)
    print("  XtremeCare — Medication Adherence Verification")
    print("=" * 57)
    print("  SPACE  →  simulate dose dispense")
    print("  Q      →  quit")
    print("=" * 57)

    active_session: VerificationSession | None = None
    dispensed_at:   str | None                 = None
    face_confirmed_in_session                  = False
    hand_detected_in_session                   = False

    result_display_until = 0.0
    last_status: str | None = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Frame read failed.")
            break

        session_name = get_session_from_time()

        # ── Stage 1: face detection (every frame) ───────────────────────
        face_ok, _conf, _bbox = detect_patient(frame)

        # ── Stage 2: verification session ───────────────────────────────
        if active_session is not None and not active_session.is_complete():
            if face_ok:
                face_confirmed_in_session = True
            if active_session.hand_detected:
                hand_detected_in_session = True

            active_session.update(frame)

            if active_session.is_complete():
                finalise_session(
                    session        = active_session,
                    dispensed_at   = dispensed_at,
                    session_name   = session_name,
                    face_confirmed = face_confirmed_in_session,
                    hand_detected  = hand_detected_in_session,
                )
                last_status          = active_session.status
                result_display_until = time.time() + 3.0

        # Clear session after 3-second result display
        if (active_session is not None
                and active_session.is_complete()
                and time.time() > result_display_until):
            active_session            = None
            dispensed_at              = None
            face_confirmed_in_session = False
            hand_detected_in_session  = False
            print("[MAIN] Ready for next dose event.")

        # ── HUD ─────────────────────────────────────────────────────────
        show_last = last_status if time.time() < result_display_until else None
        draw_hud(frame, session_name, face_ok, active_session, show_last)

        cv2.imshow("XtremeCare — Medication Verification", frame)

        # ── Keyboard ────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), ord('Q')):
            print("[MAIN] Quit.")
            break

        if key == ord(' '):
            if active_session is not None and not active_session.is_complete():
                print("[MAIN] Session already active — ignoring SPACE.")
                continue

            session_name              = get_session_from_time()
            dispensed_at              = get_timestamp()
            face_confirmed_in_session = False
            hand_detected_in_session  = False
            last_status               = None
            active_session            = VerificationSession(session_name)

            print(f"[MAIN] Dose event triggered — session: {session_name}")
            print(f"[MAIN] Dispensed at: {dispensed_at}")
            post_dose_event(PATIENT_ID, session_name, dispensed_at)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

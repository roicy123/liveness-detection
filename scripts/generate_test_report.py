import json

def calculate_iso_metrics(reports):
    """
    APCER: Attack Presentation Classification Error Rate (Spoof accepted as Live)
    BPCER: Bona Fide Presentation Classification Error Rate (Live rejected as Spoof)
    """
    attacks_total = 0
    attacks_accepted = 0
    
    bona_fide_total = 0
    bona_fide_rejected = 0
    
    for report in reports:
        actual = report["actual"]
        predicted = report["predicted"]
        
        if actual == "spoof_attack":
            attacks_total += 1
            if predicted == "live_person":
                attacks_accepted += 1
        elif actual == "live_person":
            bona_fide_total += 1
            if predicted != "live_person":
                bona_fide_rejected += 1
                
    apcer = (attacks_accepted / attacks_total) if attacks_total > 0 else 0.0
    bpcer = (bona_fide_rejected / bona_fide_total) if bona_fide_total > 0 else 0.0
    acer = (apcer + bpcer) / 2
    
    return apcer, bpcer, acer

import os
import cv2
from app.services.face_detector import detect_face, FaceDetectionError
from app.services.passive_liveness import evaluate_passive_liveness
from app.services.spoof_detector import evaluate_spoofing
from app.services.decision_fusion import fuse_session_decisions

if __name__ == "__main__":
    # We will look for labels.json
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
    labels_path = os.path.join(fixtures_dir, "labels.json")
    
    reports = []
    
    if not os.path.exists(labels_path):
        print(f"Error: {labels_path} not found. Please provide a labels.json or run the synthetic generator script.")
    else:
        with open(labels_path, "r") as f:
            labels = json.load(f)
            
        print("Running Spoof-Attack Eval Suite on real inputs...")
        
        real_images_found = False
        
        for filename, actual_label in labels.items():
            if "live.jpg" in filename or "print_attack.jpg" in filename:
                real_images_found = True
                
            path = os.path.join(fixtures_dir, filename)
            if not os.path.exists(path):
                print(f"File {filename} missing, skipping.")
                continue
                
            img = cv2.imread(path)
            
            # Dummy session data for passive checks
            session_data = {"accumulated_data": {}}
            
            try:
                face_data = detect_face(img)
                passive_scores = evaluate_passive_liveness(img, face_data, session_data)
                
                # Mock a passed active score to isolate passive performance
                session_data["accumulated_data"]["active_pass_count"] = 3
                session_data["challenges"] = ["blink", "smile", "turn_left"]
                session_data["accumulated_data"]["passive_scores"] = [passive_scores]
                
                spoof_scores = evaluate_spoofing(passive_scores, session_data)
                session_data["accumulated_data"]["spoof_scores"] = [spoof_scores]
                
                fusion = fuse_session_decisions(session_data)
                predicted = fusion["classification"]
            except FaceDetectionError:
                # If no face, it's definitely unable to verify / rejected
                predicted = "unable_to_verify"
                
            print(f"File: {filename:25s} | Actual: {actual_label:15s} | Predicted: {predicted}")
            reports.append({"actual": actual_label, "predicted": predicted})
            
        if not real_images_found:
            print("\nWARNING: Evaluated against synthetic samples only — APCER/BPCER are ")
            print("not representative of real-world performance until real fixture images")
            print("are supplied (e.g. live.jpg, print_attack.jpg) by a human. See tests/fixtures/README.md.")
            
        apcer, bpcer, acer = calculate_iso_metrics(reports)
        
        print("\n==============================")
        print("ISO/IEC 30107-3 Metrics Report (PROVISIONAL)")
        print("==============================")
        print(f"APCER (Attack Presentation Classification Error Rate): {apcer:.2%}")
        print(f"BPCER (Bona Fide Presentation Classification Error Rate): {bpcer:.2%}")
        print(f"ACER (Average Classification Error Rate): {acer:.2%}")

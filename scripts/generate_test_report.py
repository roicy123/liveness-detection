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

if __name__ == "__main__":
    # Sample data for demonstration
    sample_reports = [
        {"actual": "live_person", "predicted": "live_person"},
        {"actual": "live_person", "predicted": "unable_to_verify"}, # False reject
        {"actual": "spoof_attack", "predicted": "spoof_attack"},
        {"actual": "spoof_attack", "predicted": "live_person"} # False accept
    ]
    
    print("Running Spoof-Attack Eval Suite...")
    print("Evaluating against test set...")
    apcer, bpcer, acer = calculate_iso_metrics(sample_reports)
    
    print("\n==============================")
    print("ISO/IEC 30107-3 Metrics Report")
    print("==============================")
    print(f"APCER (Attack Presentation Classification Error Rate): {apcer:.2%}")
    print(f"BPCER (Bona Fide Presentation Classification Error Rate): {bpcer:.2%}")
    print(f"ACER (Average Classification Error Rate): {acer:.2%}")

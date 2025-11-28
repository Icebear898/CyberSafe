"""
Evidence logging service for screenshots and incident tracking
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from app.core.config import settings


class EvidenceLogger:
    def __init__(self):
        self.evidence_dir = Path(settings.EVIDENCE_DIR)
        self.screenshot_dir = Path(settings.SCREENSHOT_DIR)
        self.logs_dir = Path(settings.LOGS_DIR)
        
        # Create directories
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def save_screenshot(self, screenshot_data: bytes, incident_id: int) -> str:
        """Save screenshot and return path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"incident_{incident_id}_{timestamp}.png"
        filepath = self.screenshot_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(screenshot_data)
        
        return str(filepath)
    
    def log_incident(
        self,
        user_id: int,
        message_id: Optional[int],
        severity: str,
        detected_content: str,
        ai_analysis: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict:
        """Log an incident to JSON file"""
        timestamp = datetime.now()
        incident_data = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "message_id": message_id,
            "severity": severity,
            "detected_content": detected_content,
            "ai_analysis": ai_analysis,
            "screenshot_path": screenshot_path,
            "context": context
        }
        
        # Save to log file
        log_filename = f"incident_{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        log_filepath = self.logs_dir / log_filename
        
        with open(log_filepath, "w") as f:
            json.dump(incident_data, f, indent=2)
        
        return incident_data
    
    def generate_report(self, user_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Generate a report from logged incidents"""
        reports = []
        
        # Read all log files
        for log_file in self.logs_dir.glob("incident_*.json"):
            try:
                with open(log_file, "r") as f:
                    incident = json.load(f)
                    
                    # Filter by user_id if provided
                    if user_id and incident.get("user_id") != user_id:
                        continue
                    
                    # Filter by date range if provided
                    if start_date or end_date:
                        incident_date = datetime.fromisoformat(incident["timestamp"])
                        if start_date and incident_date < datetime.fromisoformat(start_date):
                            continue
                        if end_date and incident_date > datetime.fromisoformat(end_date):
                            continue
                    
                    reports.append(incident)
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
        
        # Sort by timestamp
        reports.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Generate summary
        summary = {
            "total_incidents": len(reports),
            "by_severity": {},
            "by_user": {}
        }
        
        for report in reports:
            severity = report.get("severity", "unknown")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            uid = report.get("user_id")
            if uid:
                summary["by_user"][uid] = summary["by_user"].get(uid, 0) + 1
        
        return {
            "summary": summary,
            "incidents": reports
        }


# Global instance
evidence_logger = EvidenceLogger()


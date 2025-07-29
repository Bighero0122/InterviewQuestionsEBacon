import json
import re
import os
from datetime import datetime

def load_jsonc_data(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'//.*', '', content)
    
    return json.loads(content)

def calculate_hours(start_str, end_str):
    start = datetime.fromisoformat(start_str.replace(' ', 'T'))
    end = datetime.fromisoformat(end_str.replace(' ', 'T'))
    return (end - start).total_seconds() / 3600

def calculate_payroll(data):
    job_rates = {job['job']: job for job in data['jobMeta']}
    results = {}
    
    for employee_data in data['employeeData']:
        name = employee_data['employee']
        
        # Create a list of punches with calculated hours and sort chronologically
        punches = []
        for punch in employee_data['timePunch']:
            hours = calculate_hours(punch['start'], punch['end'])
            job_info = job_rates[punch['job']]
            punches.append({
                'start': punch['start'],
                'hours': hours,
                'rate': job_info['rate'],
                'benefits_rate': job_info['benefitsRate']
            })
        
        # Sort by start time (chronological order)
        punches.sort(key=lambda x: x['start'])
        
        # Apply rates chronologically
        total_hours = 0
        total_wages = 0
        total_benefits = 0
        regular_hours = 0
        overtime_hours = 0
        doubletime_hours = 0
        
        for punch in punches:
            hours = punch['hours']
            rate = punch['rate']
            benefits_rate = punch['benefits_rate']
            
            # Calculate benefits (always at regular rate regardless of overtime)
            total_benefits += hours * benefits_rate
            
            # Apply wage rates based on cumulative hours
            hours_remaining = hours
            punch_start_hour = total_hours
            
            while hours_remaining > 0:
                current_hour = punch_start_hour + (hours - hours_remaining)
                
                if current_hour < 40:
                    # Regular time
                    regular_chunk = min(hours_remaining, 40 - current_hour)
                    regular_hours += regular_chunk
                    total_wages += regular_chunk * rate
                    hours_remaining -= regular_chunk
                    
                elif current_hour < 48:
                    # Overtime (1.5x)
                    overtime_chunk = min(hours_remaining, 48 - current_hour)
                    overtime_hours += overtime_chunk
                    total_wages += overtime_chunk * rate * 1.5
                    hours_remaining -= overtime_chunk
                    
                else:
                    # Double time (2.0x)
                    doubletime_hours += hours_remaining
                    total_wages += hours_remaining * rate * 2.0
                    hours_remaining = 0
            
            total_hours += hours
        
        results[name] = {
            'employee': name,
            'regular': f"{regular_hours:.4f}",
            'overtime': f"{overtime_hours:.4f}",
            'doubletime': f"{doubletime_hours:.4f}",
            'wageTotal': f"{total_wages:.4f}",
            'benefitTotal': f"{total_benefits:.4f}"
        }
    
    return results

if __name__ == "__main__":
    data = load_jsonc_data('PunchLogicTest.jsonc')
    results = calculate_payroll(data)
    print(json.dumps(results, indent=2))
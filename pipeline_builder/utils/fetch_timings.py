import sys
import numbers


class Timer:
    def __init__(self):
        pass

    def get_timings(self):
        print("\nSelect the type of activity \n1. Interval Based \n2. Time Based")
        activity_type = input("\nSelect the option number [1/2]: ")

        if activity_type == "1":
            timing = input("Select the Interval [format: 60s, 90m, 1h]: ")
            timing_string = f"interval: {timing}"
        elif activity_type == "2":
            timing = input("Select the Timing [format: 3:04 PM, 3PM, 3PM, 15:04, and 1504]: ")
            timing_string = f"start: '{timing}' \n   stop: '{timing}'"
        else:
            print("Wrong Input given")
            sys.exit(1)

        print("\nSelect the days on which pipeline needs to be triggered ")
        day_of_week = {"1": "Monday","2": "Tuesday","3": "Wednesday","4": "Thursday","5": "Friday","6": "Saturday","7": "Sunday"}
        for k,v in day_of_week.items():
            print(f"{k}. {v}")
        days = input("\nSelect the day options from 1 to 7 [comma seperated] or Press Enter to select all days: ")
        days_data = []

        if days == '':
            days_data = ["Monday", "Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        else:
            days_data.extend(day_of_week[f"{data}"] for data in days.split(","))

        return timing_string, f"days: {days_data}"

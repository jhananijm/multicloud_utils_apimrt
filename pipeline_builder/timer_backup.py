import sys
import numbers

# def main():
#     print("Select the type of activity\n1.Daily2.particular days of a week")
#     activity_type = input("Select the option number [1/2]")

#     if activity_type not in ['1','2']:
#         print("Wrong Input given")
#         sys.exit(1)

#     if activity_type == "1":
#         print("Select the type of trigger\n1. Time based [format: 3:00 PM]2.")

def main():
    day_of_week = {"1": "Monday","2": "Tuesday","3": "Wednesday","4": "Thursday","5": "Friday","6": "Saturday","7": "Sunday"}
    param = "/5 2 * * 1-4"
    day_string = []
    interval_flag = False
    min_time = ""
    interval = param.split()
    if "/" in interval[0]:
        data = interval[0].split("/")
        min_time = f"{data[1]}m"
        interval_flag = True
    elif "*" in interval[0]:
        min_time = "00m"
    else:
        min_time = f"{interval[0]}m"

    
    if "/" in interval[1]:
        data = interval[1].split("/")
        hour_time = f"{data[1]}h"
        interval_flag = True
    elif "*" in interval[1]:
        hour_time = "00h"
    else:
        hour_time = f"{interval[1]}h"

    if "-" in interval[4]:
        data = interval[4].split("-")
        for i in range(int(data[0]), int(data[1]) + 1):
            day_string.append(day_of_week[str(i)])
    elif "," in interval[4]:
        for i in interval[4].split(","):
            day_string.append(day_of_week[i])
    elif interval[4].isnumeric():
        day_string.append(day_of_week[interval[4]])
    
    print(day_string)

    print(f"{hour_time} {min_time}")

    if interval_flag:
        #generated_time = {interval: f"{hour_time} {min_time}"}
        print(f"Pipeline will be triggered at at interval of {hour_time} {min_time} daily")
    else:
        pass


if __name__ == "__main__":
    main()
import datetime

data_list = [("12:23:58", 30), ("12:23:59", 30), ("12:24:01", 30)]

# 시간 문자열을 datetime 객체로 변환하는 함수
def str_to_datetime(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M:%S")

# 누락된 시간대를 찾아 None으로 채우는 함수
def fill_missing_data(data_list):
    filled_data_list = []
    for i in range(len(data_list)):
        if i == 0: # 첫 번째 데이터는 그대로 추가
            filled_data_list.append(data_list[i])
        else:
            prev_time = str_to_datetime(data_list[i-1][0])
            curr_time = str_to_datetime(data_list[i][0])
            time_diff = (curr_time - prev_time).total_seconds()
            if time_diff > 1: # 1초 이상 누락된 경우 None 추가
                missing_times = int(time_diff) - 1
                for j in range(missing_times):
                    missing_time = prev_time + datetime.timedelta(seconds=j+1)
                    filled_data_list.append((missing_time.strftime("%H:%M:%S"), None))
            filled_data_list.append(data_list[i])
    return filled_data_list

filled_data_list = fill_missing_data(data_list)
print(filled_data_list)

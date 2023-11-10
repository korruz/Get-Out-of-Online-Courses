import streamlit as st
import random
import time
import requests
import re
import json
from dotenv import load_dotenv
import os


def main():
    with st.sidebar:
        st.header("Configuration")

        load_dotenv()
        st.session_state["url"] = st.text_input(
            "URL: https://ahuyjs.yuketang.cn/",
            value=os.getenv("url"),
        )
        st.session_state["csrftoken"] = st.text_input(
            "CSRF Token: xxxxxx", value=os.getenv("csrftoken")
        )
        st.session_state["sessionid"] = st.text_input(
            "Session ID: xxxxxx", value=os.getenv("sessionid")
        )
        st.session_state["universityId"] = st.text_input(
            "University ID: 3524", value=os.getenv("universityId")
        )

        if "courses_options" not in st.session_state:
            st.session_state["courses_options"] = []

        st.session_state["course_name"] = st.selectbox(
            "选择课程", st.session_state["courses_options"], index=0
        )
        st.write("You selected:", st.session_state["course_name"])

        st.session_state["learning_rate"] = st.slider("学习速度", 1, 10, 4, 1)

        col_courses, col_stop, col_start = st.columns([2, 1, 1])

        update_submit_url()
        update_headers()
        get_user_id()

        with col_courses:
            st.button("获取课程列表", key="courses", on_click=get_courses_info)
        with col_start:
            st.button("运行", key="start", on_click=do_start)
        with col_stop:
            st.button("停止", key="stop", on_click=do_stop)


def do_start():
    if st.session_state["course_name"] is None:
        st.text("未选择课程")
        game_over()
        return
    for detail in st.session_state["courses_details"]:
        if detail["course_name"] == st.session_state["course_name"]:
            st.session_state["classroom_id"] = detail["classroom_id"]
            st.session_state["course_sign"] = detail["course_sign"]
            st.session_state["course_id"] = detail["course_id"]
            st.session_state["sku_id"] = detail["sku_id"]

    videos = get_videos_ids(
        st.session_state["course_name"],
        st.session_state["classroom_id"],
        st.session_state["course_sign"],
    )

    st.session_state["statue"] = True
    for video in videos.items():
        if bool(st.session_state["statue"]):
            one_video_watcher(
                video[0],
                video[1],
                st.session_state["course_id"],
                st.session_state["user_id"],
                st.session_state["classroom_id"],
                st.session_state["sku_id"],
            )
    game_over()


def game_over():
    st.text("运行结束")


def do_stop():
    st.session_state["statue"] = False
    st.text("运行停止")


def get_user_id() -> bool:
    # 首先要获取用户的个人ID，即user_id,该值在查询用户的视频进度时需要使用
    user_id_url = st.session_state["url"] + "edu_admin/check_user_session/"
    id_response = requests.get(
        url=user_id_url, headers=dict(st.session_state["headers"])
    )
    try:
        st.session_state["user_id"] = (
            re.search(r'"user_id":(.+?)}', id_response.text).group(1).strip()
        )
    except:
        return False
    return True


def get_courses_info():
    st.session_state["courses_details"] = get_courses()
    st.session_state["courses_options"] = get_course_name(
        st.session_state["courses_details"]
    )


def get_course_name(courses):
    return [course["course_name"] for course in courses]


def get_courses() -> list:
    all_courses = []
    get_classroom_id = (
        st.session_state["url"]
        + "mooc-api/v1/lms/user/user-courses/?status=1&page=1&no_page=1&term=latest&uv_id="
        + st.session_state["universityId"]
        + ""
    )
    print(get_classroom_id)
    classroom_id_response = requests.get(
        url=get_classroom_id, headers=st.session_state["headers"]
    )
    try:
        for ins in json.loads(classroom_id_response.text)["data"]["product_list"]:
            all_courses.append(
                {
                    "course_name": ins["course_name"],
                    "classroom_id": ins["classroom_id"],
                    "course_sign": ins["course_sign"],
                    "sku_id": ins["sku_id"],
                    "course_id": ins["course_id"],
                }
            )
    except Exception as e:
        print("fail while getting classroom_id!!! please re-run this program!")
        raise Exception(
            "fail while getting classroom_id!!! please re-run this program!"
        )
    return all_courses


def get_videos_ids(course_name, classroom_id, course_sign):
    get_homework_ids = (
        st.session_state["url"]
        + "mooc-api/v1/lms/learn/course/chapter?cid="
        + str(classroom_id)
        + "&term=latest&uv_id="
        + st.session_state["universityId"]
        + "&sign="
        + course_sign
    )
    homework_ids_response = requests.get(
        url=get_homework_ids, headers=st.session_state["headers"]
    )
    homework_json = json.loads(homework_ids_response.text)
    homework_dic = {}
    try:
        for i in homework_json["data"]["course_chapter"]:
            for j in i["section_leaf_list"]:
                if "leaf_list" in j:
                    for z in j["leaf_list"]:
                        if z["leaf_type"] == leaf_type["video"]:
                            homework_dic[z["id"]] = z["name"]
                else:
                    if j["leaf_type"] == leaf_type["video"]:
                        # homework_ids.append(j["id"])
                        homework_dic[j["id"]] = j["name"]
        print(course_name + "共有" + str(len(homework_dic)) + "个视频喔！")
        return homework_dic
    except:
        print("fail while getting homework_ids!!! please re-run this program!")
        raise Exception(
            "fail while getting homework_ids!!! please re-run this program!"
        )


def one_video_watcher(video_id, video_name, cid, user_id, classroomid, skuid):
    st.text("正在处理视频: " + video_name)
    progress_bar = st.progress(0)
    video_id = str(video_id)
    classroomid = str(classroomid)
    st.session_state["url_video_log_base"] = (
        str(st.session_state["url"]) + "video-log/heartbeat/"
    )
    get_url = (
        st.session_state["url"]
        + "video-log/get_video_watch_progress/?cid="
        + str(cid)
        + "&user_id="
        + str(user_id)
        + "&classroom_id="
        + str(classroomid)
        + "&video_type=video&vtype=rate&video_id="
        + str(video_id)
        + "&snapshot=1&term=latest&uv_id="
        + st.session_state["universityId"]
        + ""
    )
    print("url: " + get_url)
    progress = requests.get(url=get_url, headers=dict(st.session_state["headers"]))
    if_completed = "0"
    try:
        if_completed = re.search(r'"completed":(.+?),', progress.text).group(1)
    except:
        pass
    if if_completed == "1":
        progress_bar.progress(100)
        print(video_name + "已经学习完毕，跳过")
        return 1
    else:
        print(video_name + "，尚未学习，现在开始自动学习")

    # 默认为0（即还没开始看）
    video_frame = 0
    val = 0
    # 获取实际值（观看时长和完成率）
    try:
        print("into")
        print(progress.text)
        res_rate = json.loads(progress.text)
        print("into2")
        tmp_rate = res_rate["data"][video_id]["rate"]
        print("into3")
        if tmp_rate is None:
            return 0
        val = tmp_rate
        print("into4")
        video_frame = res_rate["data"][str(video_id)]["watch_length"]
        print("video_frame: " + video_frame)
    except Exception as e:
        print(e.__str__())

    t = time.time()
    timstap = int(round(t * 1000))
    heart_data = []
    while float(val) <= 0.95:
        for i in range(3):
            heart_data.append(
                {
                    "i": 5,
                    "et": "loadeddata",
                    "p": "web",
                    "n": "ali-cdn.xuetangx.com",
                    "lob": "cloud4",
                    "cp": video_frame,
                    "fp": 0,
                    "tp": 0,
                    "sp": 2,
                    "ts": str(timstap),
                    "u": int(user_id),
                    "uip": "",
                    "c": cid,
                    "v": int(video_id),
                    "skuid": skuid,
                    "classroomid": classroomid,
                    "cc": video_id,
                    "d": 4976.5,
                    "pg": video_id
                    + "_"
                    + "".join(random.sample("zyxwvutsrqponmlkjihgfedcba1234567890", 4)),
                    "sq": i,
                    "t": "video",
                }
            )
            video_frame += int(st.session_state["learning_rate"])
        data = {"heart_data": heart_data}
        r = requests.post(
            url=st.session_state["url_video_log_base"],
            headers=dict(st.session_state["headers"]),
            json=data,
        )
        heart_data = []
        try:
            delay_time = (
                re.search(r"Expected available in(.+?)second.", r.text).group(1).strip()
            )
            print("由于网络阻塞，万恶的雨课堂，要阻塞" + str(delay_time) + "秒")
            time.sleep(float(delay_time) + 0.5)
            print("恢复工作啦～～")
            r = requests.post(
                url=st.session_state["submit_url"],
                headers=st.session_state["headers"],
                data=data,
            )
        except:
            pass
        try:
            progress = requests.get(url=get_url, headers=st.session_state["headers"])
            res_rate = json.loads(progress.text)
            tmp_rate = res_rate["data"][video_id]["rate"]
            if tmp_rate is None:
                return 0
            val = str(tmp_rate)
            progress_bar.progress(str(float(val) * 100))
            print(
                "视频"
                + video_id
                + " "
                + video_name
                + " 学习进度为：\t"
                + str(float(val) * 100)
                + "%/100%"
            )
            time.sleep(2)
        except Exception as e:
            print(e.__str__())
            pass
    print("视频" + video_id + " " + video_name + "学习完成！")
    return 1


def update_submit_url():
    st.session_state["submit_url"] = (
        st.session_state["url"]
        + "mooc-api/v1/lms/exercise/problem_apply/?term=latest&uv_id="
        + st.session_state["universityId"]
        + ""
    )


def update_headers():
    st.session_state["headers"] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
        "Content-Type": "application/json",
        "Cookie": "csrftoken="
        + st.session_state["csrftoken"]
        + "; sessionid="
        + st.session_state["sessionid"]
        + "; university_id="
        + st.session_state["universityId"]
        + "; platform_id=3",
        "x-csrftoken": st.session_state["csrftoken"],
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "university-id": st.session_state["universityId"],
        "xtbz": "cloud",
    }


leaf_type = {"video": 0, "homework": 6, "exam": 5, "recommend": 3, "discussion": 4}


if __name__ == "__main__":
    st.set_page_config(
        page_title="Get Out of Online Courses", page_icon=":chart_with_upwards_trend:"
    )
    main()

def video():
    url = "https://www.w3schools.com/html/mov_bbb.mp4"
    file = requests.get(url).content
    st.video(file)
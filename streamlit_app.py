import streamlit as st
import json
from datetime import datetime
import random
import re

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Tweet Viewer for Discourse Analysis")

# --- Load Data ---
@st.cache_data
def load_data():
    with open("tweets.json", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# --- Utilities ---
def safe_parse_date(tweet):
    try:
        return datetime.fromisoformat(tweet.get("tweetDate").replace("Z", "+00:00"))
    except:
        return datetime.min

data.sort(key=safe_parse_date)

# --- Session State Initialization ---
if "index" not in st.session_state:
    st.session_state.index = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = {}
if "filter_tag" not in st.session_state:
    st.session_state.filter_tag = ""
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = set()
if "show_only_bookmarked" not in st.session_state:
    st.session_state.show_only_bookmarked = False

# --- Filtering Setup ---
st.sidebar.header("🔍 Filters")

tag_options = list(set(
    ann["tag"] for ann in st.session_state.annotations.values() if ann.get("tag")
))
tag_filter = st.sidebar.selectbox("Filter by tag:", ["All"] + sorted(tag_options))
search_keyword = st.sidebar.text_input("Search content keyword:")
date_range = st.sidebar.text_input("Filter by date range:", "YYYY/MM/DD - YYYY/MM/DD")

# Toggle bookmarked view
if st.sidebar.checkbox("⭐ Show Bookmarked Only"):
    st.session_state.show_only_bookmarked = True
else:
    st.session_state.show_only_bookmarked = False

# --- Determine Displayed Tweet Indexes ---
filtered_indices = list(range(len(data)))

if tag_filter != "All":
    filtered_indices = [
        i for i in filtered_indices
        if i in st.session_state.annotations and st.session_state.annotations[i].get("tag") == tag_filter
    ]

if search_keyword:
    filtered_indices = [
        i for i in filtered_indices if search_keyword in data[i].get("content", "")
    ]

if date_range and "-" in date_range:
    try:
        start_str, end_str = date_range.split("-")
        start_date = datetime.strptime(start_str.strip(), "%Y/%m/%d")
        end_date = datetime.strptime(end_str.strip(), "%Y/%m/%d")
        filtered_indices = [
            i for i in filtered_indices
            if start_date <= safe_parse_date(data[i]) <= end_date
        ]
    except:
        pass

if st.session_state.show_only_bookmarked:
    filtered_indices = [i for i in filtered_indices if i in st.session_state.bookmarks]

if not filtered_indices:
    st.warning("No tweets match your filters.")
    st.stop()

# Ensure current index is valid
if st.session_state.index not in filtered_indices:
    st.session_state.index = filtered_indices[0]

# --- Current Tweet ---
current_index = st.session_state.index
current_position = filtered_indices.index(current_index)
tweet = data[current_index]

content = tweet.get("content", "")
date = tweet.get("tweetDate", "Unknown date")
url = tweet.get("tweetUrl", "")
profile_url = tweet.get("Twitter Profile", "")

user = profile_url.split("twitter.com/")[-1].strip("/") if "twitter.com/" in profile_url else "Unknown user"

# --- Layout ---
col1, col2 = st.columns([2, 2])

with col1:
    st.title("📒 Tweet Viewer for Discourse Analysis")
    st.caption("Use this tool to annotate tweets, verify user info, and preview posts side-by-side.")

    st.markdown(f"**Tweet {current_index+1}/{len(data)}**")
    st.markdown(f"📅 **Date:** {date}")
    user_input = st.text_input("👤 @ Username (editable):", user, key="user")
    st.markdown(f"[🔗 View Tweet Link]({url})")

    st.markdown(
        f"""
        <div style='background-color:#f9f9f9;padding:15px;border-radius:10px;
                    font-size:22px;line-height:1.8;direction:rtl'>
            {content}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.text_input("Add a tag (e.g., grief, support, silencing)", key="tag")
    st.text_area("Notes", key="note")

    bookmark_label = "⭐ Remove Bookmark" if current_index in st.session_state.bookmarks else "⭐ Bookmark"
    if st.button(bookmark_label):
        if current_index in st.session_state.bookmarks:
            st.session_state.bookmarks.remove(current_index)
        else:
            st.session_state.bookmarks.add(current_index)

    if st.button("💾 Save Tag and Note"):
        st.session_state.annotations[current_index] = {
            "tag": st.session_state.tag,
            "note": st.session_state.note,
            "content": content,
            "date": date,
            "user": st.session_state.user,
            "url": url
        }
        st.success("Saved!")

    col_prev, col_rand, col_next = st.columns([1, 1, 1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.index = filtered_indices[max(0, current_position - 1)]
    with col_rand:
        if st.button("🎲 Random"):
            st.session_state.index = random.choice(filtered_indices)
    with col_next:
        if st.button("➡️ Next"):
            st.session_state.index = filtered_indices[min(len(filtered_indices) - 1, current_position + 1)]

    if st.button("📤 Export All Annotations"):
        with open("annotations_export.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.annotations, f, ensure_ascii=False, indent=2)
        st.success("Annotations exported to annotations_export.json")

with col2:
    st.subheader("📍 Tweet Preview")
    if url:
        tweet_embed_html = f"""
            <blockquote class="twitter-tweet">
                <a href="{url}"></a>
            </blockquote>
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        """
        st.components.v1.html(tweet_embed_html, height=600)
    else:
        st.warning("No URL found for this tweet.")
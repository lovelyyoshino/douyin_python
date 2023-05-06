from websocket import WebSocketApp
import json
import base64
import re
from urllib.parse import unquote_plus
import requests
import new_pb2 as pb
import execjs
ctx=execjs.compile(open('get_handle.js','r').read())
ctx2=execjs.compile(open('wss_sign.js','r',encoding='utf8').read())

pushproto_PushFrame = pb.pushproto_PushFrame()
pushproto_PushFrame.payloadtype = "hb"
ping_byte = pushproto_PushFrame.SerializeToString()
# print(ping_byte)

def fetch_live_room_info(url):
    s=requests.session()
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    }
    response = s.get(url, headers=headers)
    cookies_dict = dict(response.cookies)
    response = s.get(url, headers=headers, cookies=cookies_dict)
    ttwid = dict(response.cookies).get('ttwid')
    data_string = re.findall(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', response.text)[0]
    data_dict = json.loads(unquote_plus(data_string))
    room_id = data_dict['app']['initialState']['roomStore']['roomInfo']['roomId']
    room_title = data_dict['app']['initialState']['roomStore']['roomInfo']["room"]['title']
    room_user_count = data_dict['app']['initialState']['roomStore']['roomInfo']["room"]['user_count_str']
    wss_url = f"wss://webcast3-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{room_id}|wss_push_did:7194466010916898342|dim_log_id:2023031913364589780C64C4339D41A267|fetch_time:1679204206030|seq:1|wss_info:0-1679204206030-0-0|wrds_kvs:DoubleLikeSyncData-1679199122146303909_WebcastRoomStatsMessage-1679204201351366602_HighlightContainerSyncData-36_WebcastRoomRankMessage-1679204165374499420_InputPanelComponentSyncData-1679198799827628222&cursor=t-1679204206030_r-1_d-1_u-1_h-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&maxCacheMessageNumber=20&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id=7194466010916898342&device_platform=web&cookie_enabled=true&screen_width=1536&screen_height=864&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/111.0.0.0%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={room_id}&heartbeatDuration=0&signature={ctx2.call('test', f',live_id=1,aid=6383,version_code=180800,webcast_sdk_version=1.3.0,room_id={room_id},sub_room_id=,sub_channel_id=,did_rule=3,user_unique_id=7194466010916898342,device_platform=web,device_type=,ac=,identity=audience')}"
    # print(wss_url)
    # print(wss_url)
    # print(room_id, room_title, room_user_count)
    return room_id, room_title, room_user_count, wss_url, ttwid



def keymessage(ws,byte,logid,payloadtype):
    webcast_im_Response = pb.webcast_im_Response()
    webcast_im_Response.ParseFromString(byte)
    # print(webcast_im_Response)
    for item in webcast_im_Response.messages:
        # print(item.method)
        if item.method == 'WebcastMemberMessage':
            webcast_im_MemberMessage = pb.webcast_im_MemberMessage()
            webcast_im_MemberMessage.ParseFromString(item.payload)
            # print(webcast_im_MemberMessage)
            try:
                nickname = webcast_im_MemberMessage.user.nickname
                text = webcast_im_MemberMessage.common.displaytext.defaultpattern.strip('{0:user} ').strip('{1:string}')
                print(nickname+':'+text)
            except:
                pass
        if item.method == 'WebcastChatMessage':
            webcast_im_ChatMessage = pb.webcast_im_ChatMessage()
            webcast_im_ChatMessage.ParseFromString(item.payload)
            # print(webcast_im_ChatMessage)
            try:
                nickname = webcast_im_ChatMessage.user.nickname
                # print(nickname)
                content = webcast_im_ChatMessage.content
                # print(content)
                print(nickname, ':', content)
            except:
                pass
        if item.method == 'WebcastGiftMessage':
            webcast_im_GiftMessage = pb.webcast_im_GiftMessage()
            webcast_im_GiftMessage.ParseFromString(item.payload)
            # print(webcast_im_GiftMessage)
            print(webcast_im_GiftMessage.common.describe)
            try:
                user = webcast_im_GiftMessage.user.nickname
                gift = webcast_im_GiftMessage.gift.name
                # print(webcast_im_GiftMessage.common.describe)
            except:
                pass
        if item.method == 'WebcastSocialMessage':
            webcast_im_SocialMessage = pb.webcast_im_SocialMessage()
            webcast_im_SocialMessage.ParseFromString(item.payload)
            try:
                user = webcast_im_SocialMessage.user.nickname
                text = webcast_im_SocialMessage.common.displaytext.defaultpattern.strip('{0:user} ')
                # print(webcast_im_SocialMessage)
                print(user,text)
            except:
                pass
        if item.method == 'WebcastLikeMessage':
            webcast_im_LikeMessage = pb.webcast_im_LikeMessage()
            webcast_im_LikeMessage.ParseFromString(item.payload)
            try:
                user = webcast_im_LikeMessage.user.nickname
                # print(user)
                text = webcast_im_LikeMessage.common.displaytext.pieces[-1].stringvalue
                # print(text)
                print(user,text)

            except:
                pass
            # print(webcast_im_LikeMessage)
        if item.method == 'WebcastRoomStatsMessage':
            webcast_im_RoomStatsMessage = pb.webcast_im_RoomStatsMessage()
            webcast_im_RoomStatsMessage.ParseFromString(item.payload)
            print(webcast_im_RoomStatsMessage)
    needack = webcast_im_Response.needack
    # print(needack)
    if needack:
        internalext = webcast_im_Response.internalext
        print(webcast_im_Response.cursor)
        ackpayload = ctx.call('get_ackpayload', internalext)
        # print(ackpayload)
        ackpayload = base64.b64decode(ackpayload)
        # print(ackpayload)
        pushproto_PushFrame2 = pb.pushproto_PushFrame()
        pushproto_PushFrame2.payloadtype = 'ack'
        pushproto_PushFrame2.payload = ackpayload
        pushproto_PushFrame2.logid = logid
        # print(pushproto_PushFrame2.SerializeToString())
        ws.send(pushproto_PushFrame2.SerializeToString())
    if payloadtype == 'close':
        ws.close()

def on_open(ws):
    print('连接成功！！！')
    ws.send(ping_byte)


def on_message(ws, content):
    # print('已获得数据：')
    pushproto_PushFrame.ParseFromString(content)
    logid=pushproto_PushFrame.logid
    payloadtype=pushproto_PushFrame.payloadtype
    # print(pushproto_PushFrame.headers)
    headers_list = {}
    for item in pushproto_PushFrame.headers:
        headers_list[item.key] = item.value
    # print(headers_list)
    if 'compress_type' in headers_list and headers_list['compress_type'] == 'gzip':
        payload = pushproto_PushFrame.payload
        payload = base64.b64encode(payload).decode()
        string = ctx.call('handle', payload)
        byte = base64.b64decode(string)
        keymessage(ws,byte,logid,payloadtype)
    else:
        payload = pushproto_PushFrame.payload
        keymessage(ws, payload, logid,payloadtype)


def on_ping(ws):
    ws.send(ping_byte)



def on_error(ws,errormessag):
    print("on_error:")
    print(errormessag)



def on_close(ws, content):
    print("连接已关闭！！！")


def run():
    web_url = "https://live.douyin.com/158341241526"

    room_id, room_title, room_user_count, wss_url, ttwid = fetch_live_room_info(web_url)
    print(f'欢迎来到{room_title}直播间，直播间人数{room_user_count}')
    ws = WebSocketApp(
        url=wss_url,
        header={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        },
        cookie=f"ttwid={ttwid}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_ping=on_ping
    )
    ws.run_forever(ping_interval=1000)


if __name__ == '__main__':
    run()

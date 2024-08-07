import pusher
app_id = "1841216"
key = "b193dcd8922273835547"
secret = "5e39e309c9ee6a995b84"
cluster = "ap1"


pusher_client = pusher.Pusher(app_id=u'1841216', key=u'b193dcd8922273835547', secret=u'5e39e309c9ee6a995b84', cluster=u'ap1')
pusher_client.trigger(u'my_channel', u'python', {u'some': u'gas'})

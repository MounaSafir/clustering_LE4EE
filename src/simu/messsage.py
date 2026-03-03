class Message:
    def __init__(self, sender, timestamp, tag, data, length = 32):
        self.sender = sender
        self.timestamp = timestamp
        self.tag = tag 
        self.data = data 
        self.length = length
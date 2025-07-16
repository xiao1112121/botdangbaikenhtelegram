        failed: List[str] = []
        
        # Tạo reply_markup từ buttons nếu có
        reply_markup = None
        if post.get('buttons'):
            keyboard = [[InlineKeyboardButton(btn['text'], url=btn['url'])] for btn in post['buttons']]
            reply_markup = InlineKeyboardMarkup(keyboard)
            print(f"DEBUG: Sending with {len(post['buttons'])} buttons")  # Debug
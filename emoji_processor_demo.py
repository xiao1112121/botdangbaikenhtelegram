#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from emoji_handler import EmojiHandler

def process_complex_emoji_text():
    """Demo xử lý emoji phức tạp và động"""
    
    # Text mẫu từ user
    sample_text = """➖➖🔫🔫🔫🔫🔥🔫🔫➖➖

📱Caros membros do ABCD.WS 📱 (http://gtt00.bet/)

🎰🎰  Abaixo estão os tempos vencedores dos Slots que o robô recomenda automaticamente para você.  Quanto mais você apostar, maior será o prêmio! Diga aos seus amigos para participarem das apostas juntos  🛶

 🔴😐🤧 CRONOGRAMA DE JOGO 😐🤧 🟠

😀 FORTUNE TIGER  (http://gtt11.bet/)😆🍎
      19:16 ⏰  19:58

😀 Captain's Bounty (http://gtt22.bet/)  (https://www.kkkk.bet/)😀
     19:25 ⏰  20:17

😀 The Great Icescape  (http://gtt33.bet/)😀
      19:41  ⏰  20:26

📱ASGARDIAN RISING  (http://gtt44.bet/)📱
       19:51 ⏰  20:43

🐃🐃🐰🐰                  🐰🐰 🐯🐯
🐃🐃🐰🐰🇧🇷🇧🇷🇧🇷🐰🐰🐯🐯 

😄😄 Faça login na sua conta de jogo ABCD.WS agora e tente a sorte. ❣️Não há limite de valor para depósitos/saques/entrada no jogo.💰 Jogadores de todo o país são muito bem-vindos para ingressar no ABCD.WS (https://t.me/+gcK1k-XJ31tiMzQ1) ! Desejo a todos um feliz jogo ~!😆😆

💬 Serviços on-line 24/7 (https://vm.vondokua.com/1kdzfz0cdixxg0k59medjggvhv)  
😂 Instagram (https://www.instagram.com/abcd.bet_ofc)
📱 WhatsApp (https://whatsapp.com/channel/0029Vb1h01J3wtb75AhXwk1C)
😀 Atividade do canal (https://t.me/abcdbetofc1)
✈️  Telegram (https://t.me/addlist/h8qn5ANrJ_1hODM1)
✈️ TG 24/7SAC (https://t.me/ABCDBETONLINE) 
💰 BAIXE RS50 (https://file.abcd.bet/app/abcdbet.apk)

🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟☺️☺️"""

    print("🔧 DEMO XỬ LÝ EMOJI PHỨC TẠP")
    print("=" * 60)
    
    # Khởi tạo emoji handler
    emoji_handler = EmojiHandler()
    
    print("📝 Văn bản gốc:")
    print(sample_text)
    print("\n" + "="*60)
    
    # Xử lý emoji
    processed_text = emoji_handler.process_text_with_emoji(sample_text)
    
    print("✨ Văn bản đã xử lý:")
    print(processed_text)
    print("\n" + "="*60)
    
    # Thống kê emoji
    emoji_count = emoji_handler.count_emoji_in_text(sample_text)
    print(f"📊 Thống kê emoji ({len(emoji_count)} loại):")
    for emoji, count in emoji_count.items():
        print(f"   {emoji} : {count} lần")
    
    print("\n" + "="*60)
    
    # Kiểm tra validation
    is_valid, issues = emoji_handler.validate_emoji_in_text(sample_text)
    print(f"✅ Validation: {'OK' if is_valid else 'CÓ VẤN ĐỀ'}")
    if issues:
        for issue in issues:
            print(f"   ⚠️ {issue}")
    
    print("\n" + "="*60)
    
    # Gợi ý emoji
    suggestions = emoji_handler.suggest_emoji_for_text(sample_text)
    print(f"💡 Gợi ý emoji phù hợp:")
    print("   " + " ".join(suggestions))
    
    return processed_text

def create_emoji_fix_patterns():
    """Tạo các pattern để sửa emoji động"""
    
    # Các pattern emoji động thường gặp
    dynamic_emoji_fixes = {
        # Emoji kết hợp
        '🔫': '🔫',  # Gun emoji
        '🎰': '🎰',  # Slot machine
        '🛶': '🛶',  # Canoe
        '🤧': '🤧',  # Sneezing face
        '🍎': '🍎',  # Apple
        '🐃': '🐃',  # Water buffalo
        '🐰': '🐰',  # Rabbit face
        '🐯': '🐯',  # Tiger face
        '🇧🇷': '🇧🇷',  # Brazil flag
        '❣️': '❣️',  # Heart exclamation
        '✈️': '✈️',  # Airplane
        '⏰': '⏰',  # Alarm clock
        
        # Emoji bị lỗi thường thấy
        '🔴': '🔴',  # Red circle
        '🟠': '🟠',  # Orange circle
        '➖': '➖',  # Heavy minus sign
        '🌟': '🌟',  # Star
        '☺️': '☺️',  # Smiling face
        
        # Emoji phức tạp
        '📱': '📱',  # Mobile phone
        '💬': '💬',  # Speech balloon
        '😂': '😂',  # Face with tears of joy
        '😀': '😀',  # Grinning face
        '😄': '😄',  # Grinning face with smiling eyes
        '😆': '😆',  # Grinning squinting face
        '😐': '😐',  # Neutral face
        '💰': '💰',  # Money bag
    }
    
    return dynamic_emoji_fixes

def advanced_emoji_processor(text):
    """Xử lý nâng cao cho emoji động"""
    
    # Sửa emoji bị encode sai
    try:
        # Decode Unicode escapes
        if '\\u' in text:
            text = text.encode().decode('unicode_escape')
    except:
        pass
    
    # Sửa emoji bị break
    text = re.sub(r'[�□]', '❓', text)
    
    # Sửa emoji skin tone bị tách
    text = re.sub(r'(👨|👩|👶|🧒|👦|👧|🧑|👴|👵)\s*🏻', r'\1🏻', text)
    text = re.sub(r'(👨|👩|👶|🧒|👦|👧|🧑|👴|👵)\s*🏼', r'\1🏼', text)
    text = re.sub(r'(👨|👩|👶|🧒|👦|👧|🧑|👴|👵)\s*🏽', r'\1🏽', text)
    text = re.sub(r'(👨|👩|👶|🧒|👦|👧|🧑|👴|👵)\s*🏾', r'\1🏾', text)
    text = re.sub(r'(👨|👩|👶|🧒|👦|👧|🧑|👴|👵)\s*🏿', r'\1🏿', text)
    
    # Sửa emoji có variant selector
    text = re.sub(r'(⏰|✈️|☺️|❣️)\s*\ufe0f', r'\1', text)
    
    # Sửa flag emoji bị tách
    text = re.sub(r'🇧\s*🇷', '🇧🇷', text)
    text = re.sub(r'🇺\s*🇸', '🇺🇸', text)
    text = re.sub(r'🇻\s*🇳', '🇻🇳', text)
    
    return text

def interactive_emoji_demo():
    """Demo tương tác xử lý emoji"""
    
    print("🎮 DEMO TƯƠNG TÁC XỬ LÝ EMOJI")
    print("=" * 60)
    print("Nhập văn bản có emoji để xử lý (hoặc 'quit' để thoát)")
    print("Ví dụ: 🔥🚀⭐ Sản phẩm mới [fire] Amazing!")
    print("=" * 60)
    
    emoji_handler = EmojiHandler()
    
    while True:
        try:
            user_input = input("\n📝 Nhập văn bản: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Tạm biệt!")
                break
            
            if not user_input:
                continue
            
            print("\n🔧 Xử lý...")
            
            # Xử lý cơ bản
            processed = emoji_handler.process_text_with_emoji(user_input)
            
            # Xử lý nâng cao
            advanced_processed = advanced_emoji_processor(processed)
            
            print(f"📤 Kết quả: {advanced_processed}")
            
            # Thống kê nhanh
            emoji_count = emoji_handler.count_emoji_in_text(user_input)
            if emoji_count:
                print(f"📊 Emoji: {len(emoji_count)} loại - {' '.join(emoji_count.keys())}")
            
            # Validation
            is_valid, issues = emoji_handler.validate_emoji_in_text(advanced_processed)
            if not is_valid:
                print(f"⚠️ Lưu ý: {', '.join(issues)}")
            
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    print("🚀 Chọn chế độ:")
    print("1. Demo xử lý văn bản mẫu")
    print("2. Demo tương tác")
    
    choice = input("Chọn (1/2): ").strip()
    
    if choice == "1":
        process_complex_emoji_text()
    elif choice == "2":
        interactive_emoji_demo()
    else:
        print("Demo xử lý văn bản mẫu:")
        process_complex_emoji_text() 
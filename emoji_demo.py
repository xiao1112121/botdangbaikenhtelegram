#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demo tính năng Emoji Handler cho Bot Đăng Bài Hàng Loạt
Giải quyết vấn đề emoji bị lỗi trên Telegram Desktop
"""

from emoji_handler import EmojiHandler

def test_emoji_processing():
    """Test xử lý emoji cơ bản"""
    print("🎨 TEST XỬ LÝ EMOJI CỞ BẢN")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    # Test shortcode
    test_cases = [
        "Khuyến mãi [fire] hôm nay!",
        "Sản phẩm [new] [star] chất lượng cao",
        "Đăng ký ngay [rocket] [money] kiếm tiền",
        "Thành công [ok] hoàn thành [thumbsup]",
        "Cảnh báo [warning] lỗi hệ thống [no]",
        "Chào mừng [heart] gia đình mới [home]",
        "Liên hệ [phone] hoặc [email] ngay!",
        "Giao hàng [car] nhanh chóng [clock]"
    ]
    
    for test_text in test_cases:
        processed = handler.process_text_with_emoji(test_text)
        print(f"Input:  {test_text}")
        print(f"Output: {processed}")
        print()

def test_emoji_suggestions():
    """Test gợi ý emoji thông minh"""
    print("🤖 TEST GỢI Ý EMOJI THÔNG MINH")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    content_examples = [
        "Khuyến mãi sốc giảm giá 50% hôm nay",
        "Sản phẩm mới ra mắt chất lượng cao",
        "Thành công đạt được mục tiêu doanh thu",
        "Chào mừng khách hàng mới tham gia",
        "Liên hệ ngay để được tư vấn miễn phí",
        "Giao hàng nhanh chóng trong ngày",
        "Đào tạo kỹ năng bán hàng chuyên nghiệp",
        "Tiệc sinh nhật vui vẻ bên gia đình",
        "Du lịch mùa hè khám phá thiên nhiên",
        "Công nghệ mới cách mạng thay đổi cuộc sống"
    ]
    
    for content in content_examples:
        suggestions = handler.suggest_emoji_for_text(content)
        print(f"Nội dung: {content}")
        print(f"Gợi ý: {' '.join(suggestions)}")
        print()

def test_emoji_validation():
    """Test validation emoji"""
    print("✅ TEST VALIDATION EMOJI")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    validation_cases = [
        "Bài viết bình thường với emoji 😊👍",
        "Quá nhiều emoji 😊😂❤️👍👏🔥💯✨🚀⭐💰🎉🎁💎👑🏆📱💻🌟🎯💡⚡🌈🔔",
        "Emoji bị lỗi � và □ trong text",
        "😊😂😍",  # Chỉ có emoji
        "Text bình thường không có emoji",
        "Emoji compound 👨‍💻👩‍🍳👨‍⚕️"
    ]
    
    for test_text in validation_cases:
        is_valid, issues = handler.validate_emoji_in_text(test_text)
        print(f"Text: {test_text}")
        print(f"Valid: {is_valid}")
        if issues:
            print(f"Issues: {', '.join(issues)}")
        print()

def test_emoji_extraction():
    """Test trích xuất emoji"""
    print("🔍 TEST TRÍCH XUẤT EMOJI")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    extract_cases = [
        "Hello 😊 world 👍 test 🔥",
        "Không có emoji nào",
        "🎉🎊🎈🎁🎂 Tiệc sinh nhật",
        "Mix text 😊 and emoji 👨‍💻 compound",
        "Emoji liên tục 😊😂😍❤️👍"
    ]
    
    for test_text in extract_cases:
        emojis = handler.extract_emoji_from_text(test_text)
        clean_text = handler.clean_text_from_emoji(test_text)
        emoji_count = handler.count_emoji_in_text(test_text)
        
        print(f"Text: {test_text}")
        print(f"Emojis: {emojis}")
        print(f"Clean text: {clean_text}")
        print(f"Count: {emoji_count}")
        print()

def test_emoji_keyboards():
    """Test emoji keyboards"""
    print("⌨️ TEST EMOJI KEYBOARDS")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    categories = ["popular", "business", "social", "food", "transport", "nature"]
    
    for category in categories:
        keyboard = handler.get_emoji_keyboard(category)
        print(f"Category: {category}")
        print(f"Keyboard rows: {len(keyboard)}")
        for i, row in enumerate(keyboard):
            print(f"  Row {i+1}: {' '.join(row)}")
        print()

def test_desktop_emoji_fixes():
    """Test sửa lỗi emoji từ desktop"""
    print("🖥️ TEST SỬA LỖI EMOJI DESKTOP")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    # Simulate broken emoji from desktop
    broken_cases = [
        "Text with broken emoji �",
        "Square emoji □ not displaying",
        "Unicode escape \\u{1F600}",
        "Compound emoji separated 👨 💻",
        "Multiple issues � and □ together",
        "Normal text with good emoji 😊"
    ]
    
    for broken_text in broken_cases:
        fixed = handler._fix_broken_emoji(broken_text)
        print(f"Broken:  {broken_text}")
        print(f"Fixed:   {fixed}")
        print()

def show_emoji_help():
    """Hiển thị hướng dẫn sử dụng emoji"""
    print("📚 HƯỚNG DẪN SỬ DỤNG EMOJI")
    print("=" * 50)
    
    handler = EmojiHandler()
    help_text = handler.get_emoji_help_text()
    print(help_text)

def interactive_demo():
    """Demo tương tác"""
    print("\n🎮 DEMO TƯƠNG TÁC")
    print("=" * 50)
    
    handler = EmojiHandler()
    
    while True:
        print("\nChọn chức năng:")
        print("1. Xử lý emoji shortcode")
        print("2. Gợi ý emoji cho nội dung")
        print("3. Validate emoji")
        print("4. Trích xuất emoji")
        print("5. Sửa lỗi emoji desktop")
        print("0. Thoát")
        
        choice = input("\nNhập lựa chọn (0-5): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            text = input("Nhập text với shortcode: ")
            processed = handler.process_text_with_emoji(text)
            print(f"Kết quả: {processed}")
        elif choice == "2":
            text = input("Nhập nội dung bài viết: ")
            suggestions = handler.suggest_emoji_for_text(text)
            print(f"Gợi ý emoji: {' '.join(suggestions)}")
        elif choice == "3":
            text = input("Nhập text để validate: ")
            is_valid, issues = handler.validate_emoji_in_text(text)
            print(f"Valid: {is_valid}")
            if issues:
                print(f"Issues: {', '.join(issues)}")
        elif choice == "4":
            text = input("Nhập text để trích xuất emoji: ")
            emojis = handler.extract_emoji_from_text(text)
            clean_text = handler.clean_text_from_emoji(text)
            print(f"Emojis: {emojis}")
            print(f"Clean text: {clean_text}")
        elif choice == "5":
            text = input("Nhập text có emoji lỗi: ")
            fixed = handler._fix_broken_emoji(text)
            print(f"Đã sửa: {fixed}")
        else:
            print("❌ Lựa chọn không hợp lệ!")

def main():
    """Chạy tất cả test"""
    print("🚀 EMOJI HANDLER DEMO")
    print("Giải quyết vấn đề emoji Telegram Desktop")
    print("=" * 60)
    
    # Chạy các test
    test_emoji_processing()
    test_emoji_suggestions()
    test_emoji_validation()
    test_emoji_extraction()
    test_emoji_keyboards()
    test_desktop_emoji_fixes()
    show_emoji_help()
    
    # Demo tương tác
    interactive_demo()

if __name__ == "__main__":
    main() 
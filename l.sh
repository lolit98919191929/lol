
yes | pkg update -y && yes | pkg upgrade -y
yes | pkg install python-pip -y
pip install selenium==4.9.1
#!/data/data/com.termux/files/usr/bin/sh
# File này sẽ thiết lập Termux, cập nhật các gói hệ thống,
# cài đặt Python, pip và các gói cần thiết để chạy script Selenium trên Termux

# Thiết lập quyền truy cập bộ nhớ
echo "Thiết lập quyền truy cập bộ nhớ..."
termux-setup-storage

# Cập nhật và nâng cấp các gói hệ thống
echo "Cập nhật hệ thống..."
pkg update -y && pkg upgrade -y

# Cài đặt Python và pip (nếu chưa cài)
echo "Cài đặt Python và pip..."
pkg install python -y
pkg install python-pip -y

# Cài đặt các tiện ích bổ sung
echo "Cài đặt wget và unzip..."
pkg install wget -y
pkg install unzip -y

# Cài đặt kho x11-repo và tur-repo để có Chromium
echo "Cài đặt x11-repo và tur-repo..."
pkg install x11-repo -y
pkg install tur-repo -y

# Cài đặt trình duyệt Chromium
echo "Cài đặt Chromium..."
pkg install chromium -y

# Cài đặt các gói Python cần thiết
echo "Cài đặt các gói Python cần thiết..."
pip install selenium==4.9.1 faker webdriver-manager requests pysocks
curl -sLf https://raw.githubusercontent.com/Yisus7u7/termux-desktop-xfce/main/boostrap.sh | bash
vncserver -listen tcp

echo "Cài đặt hoàn tất. Bạn có thể chạy script Python của bạn bằng lệnh:"
echo "python nvr.py"
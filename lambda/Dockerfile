FROM public.ecr.aws/lambda/python:3.12

# Install system deps for Playwright Chromium
RUN dnf install -y \
    atk cups-libs gtk3 libXcomposite libXcursor libXdamage \
    libXext libXi libXrandr libXScrnSaver libXtst pango \
    xorg-x11-fonts-100dpi xorg-x11-fonts-75dpi xorg-x11-fonts-cyrillic \
    xorg-x11-fonts-misc xorg-x11-fonts-Type1 xorg-x11-utils \
    alsa-lib nss nspr mesa-libgbm && \
    dnf clean all

# Install Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright Chromium only
RUN playwright install chromium

# Copy all Lambda handlers
COPY verify-license/handler.py verify_license_handler.py
COPY verify-bond/handler.py verify_bond_handler.py
COPY verify-wc/handler.py verify_wc_handler.py
COPY get-upload-url/handler.py get_upload_url_handler.py
COPY scan-card/handler.py scan_card_handler.py
COPY get-contractors/handler.py get_contractors_handler.py

# Default handler (overridden per function in SAM)
CMD ["verify_license_handler.handler"]

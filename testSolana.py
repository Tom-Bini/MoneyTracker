from seleniumbase import SB

with SB(uc=True, test=True) as sb:
    url = "https://portfolio.jup.ag/portfolio/DHmzvbLXE9HJWjS1P2SVAjTNV32sp4xWRMtbmn3TWFCi"
    sb.uc_open_with_reconnect(url, 4)
    print(sb.get_page_title())
    sb.uc_gui_click_captcha()  # Only used if needed


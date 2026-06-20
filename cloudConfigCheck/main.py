from config_scanner import scan_cloud_configurations, print_website_alerts


if __name__ == "__main__":
    alerts = scan_cloud_configurations()
    print_website_alerts(alerts)
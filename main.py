import requests
import datetime as dt
from twilio.rest import Client
import config

CURRENCY_SYMBOL = config.CURRENCY_SYMBOL
CURRENCY_API_KEY = config.CURRENCY_API_KEY
NEWS_API_KEY = config.NEWS_API_KEY
JSON_PRICE_IDENTIFIER = config.JSON_PRICE_IDENTIFIER
TWILIO_ACCOUNT_SID = config.TWILIO_ACCOUNT_SID
TWILIO_ACCOUNT_AUTH_TOKEN = config.TWILIO_ACCOUNT_AUTH_TOKEN
SENDER_PHONE = config.SENDER_PHONE
RECEIVER_PHONE = config.RECEIVER_PHONE
SMS_TEMPLATE_FILE = config.SMS_TEMPLATE_FILE

def get_dates():
    today = dt.datetime.today()
    last_closed_day = today - dt.timedelta(days=1)
    previous_last_closed_day = today - dt.timedelta(days=2)
    if dt.datetime.weekday(last_closed_day) == 5:
        last_closed_day -= dt.timedelta(days=1)
        previous_last_closed_day -= dt.timedelta(days=1)
    elif dt.datetime.weekday(last_closed_day) == 6:
        last_closed_day -= dt.timedelta(days=2)
        previous_last_closed_day -= dt.timedelta(days=2)
    elif dt.datetime.weekday(last_closed_day) == 0:
        previous_last_closed_day = last_closed_day - dt.timedelta(days=3)  # Set to Friday before the last closed day

    return last_closed_day, previous_last_closed_day


def get_news(start_date, end_date):
    news_request_string = f"https://newsapi.org/v2/everything?q=bitcoin&from={start_date}&to={end_date}&sortBy=relevancy&apiKey={NEWS_API_KEY}&language=en"
    news_data = requests.get(news_request_string)
    titles = [article["title"] for article in news_data.json()["articles"][:3]]  # Get titles of first 3 articles
    return titles


def get_btc_price(date):
    btc_price_raw = requests.get(
        f"https://api.polygon.io/v1/open-close/crypto/{CURRENCY_SYMBOL}/USD/{date}?adjusted=false&apiKey={CURRENCY_API_KEY}")
    btc_price = btc_price_raw.json()["close"]
    return btc_price


def read_sms_template():
    with open(SMS_TEMPLATE_FILE, "r") as template_file:
        return template_file.read()


def send_sms(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_ACCOUNT_AUTH_TOKEN)
    message = client.messages.create(body=message, from_=SENDER_PHONE, to=RECEIVER_PHONE)
    print(message.body)
    print(message.status)


def main():
    try:
        last_closed_day, previous_closed_day = get_dates()
        last_closed_day_formatted = str(last_closed_day).split(" ")[0]
        previous_closed_day_formatted = str(previous_closed_day).split(" ")[0]

        btc_price_last_day = get_btc_price(last_closed_day_formatted)
        btc_price_previous_day = get_btc_price(previous_closed_day_formatted)
        btc_price_today = get_btc_price(dt.datetime.today().strftime('%Y-%m-%d'))
        print(btc_price_today)
        rate_of_change = ((btc_price_last_day - btc_price_previous_day) / btc_price_last_day) * 100

        news_titles = get_news(previous_closed_day_formatted, last_closed_day_formatted)

        if abs(rate_of_change) >= 5:
            if rate_of_change < 0:
                trend = "DECREASED BY"
            else:
                trend = "INCREASED BY"

            sms_template = read_sms_template()
            message = sms_template.replace("SYMBOL", CURRENCY_SYMBOL)\
                .replace("X%", f"{trend} {rate_of_change:.2f}%")\
                .replace("[DATE1]", last_closed_day_formatted)\
                .replace("[DATE2]", previous_closed_day_formatted)\
                .replace("-PRICE", str(float(btc_price_today)))\
                .replace("TITLE1", news_titles[0])\
                .replace("TITLE2", news_titles[1])\
                .replace("TITLE3", news_titles[2])

            send_sms(message)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
from email_detector import predict_email

if __name__ == "__main__":

    print("====== EMAIL FRAUD DETECTOR ======\n")

    while True:
        email_text = input("Enter email text (type 'exit' to quit): ")

        if email_text.lower() == "exit":
            break

        result = predict_email(email_text)

        print("\n--- Result ---")
        print("Prediction:", result["prediction"])
        print("Confidence:", result["confidence"], "%")
        print("Safe Probability:", result["safe_probability"], "%")
        print("Phishing Probability:", result["phishing_probability"], "%")
        print()

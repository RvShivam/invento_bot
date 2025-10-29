import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


# Use http://localhost:8000 if your Django server and Rasa are on the same machine.
# If Django is on a different machine, use its IP address.
API_BASE_URL = "http://localhost:8000/api"

# --- Helper Functions ---

def get_response(tracker: Tracker, text_en: str, text_hi: str) -> Text:
    """Gets the correct translated response based on the language slot."""
    lang = tracker.get_slot("language") or "en"
    return text_hi if lang == "hi" else text_en

def get_auth_headers(tracker: Tracker) -> Dict[Text, Text]:
    """Extracts the JWT from the message metadata to create auth headers."""
    jwt_token = tracker.latest_message.get('metadata', {}).get('jwt_token')
    if not jwt_token:
        return None
    return {"Authorization": f"Bearer {jwt_token}"}

def find_item(product_name: str, headers: Dict) -> Dict[Text, Any]:
    """Uses the fuzzy search endpoint to find an item by name."""
    try:
        response = requests.get(f"{API_BASE_URL}/items/?search={product_name}", headers=headers)
        if response.status_code == 200:
            items = response.json()
            if items:
                return items[0]  
    except Exception as e:
        print(f"Error finding item: {e}")
    return None


class ActionSetLanguage(Action):
    def name(self) -> Text:
        return "action_set_language"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        lang = next(tracker.get_latest_entity_values("language"), None)
        if lang and lang.lower() in ["en", "hi" , "english", "hindi"]:
            lang_code = "hi" if lang.lower() == "hindi" else "en"
            message = f"Language set to {lang}." if lang_code == "en" else f"भाषा {lang} पर सेट की गई है।"
            dispatcher.utter_message(text=message)
            return [SlotSet("language", lang_code)]
        else:
            message = get_response(tracker, "Please specify a valid language: English or Hindi.", "कृपया एक मान्य भाषा निर्दिष्ट करें: अंग्रेजी या हिंदी।")
            dispatcher.utter_message(text=message)
            return []
        

class ActionCheckStock(Action):
    def name(self) -> Text:
        return "action_check_stock"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        headers = get_auth_headers(tracker)
        if not headers:
            message = get_response(tracker, "Authentication error. Please restart the chat.", "प्रमाणीकरण त्रुटि। कृपया चैट को पुनरारंभ करें।")
            dispatcher.utter_message(text=message)
            return []

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        if not product_name:
            message = get_response(tracker, "Which product would you like to check?", "आप किस उत्पाद की जानकारी चाहते हैं?")
            dispatcher.utter_message(text=message)
            return []

        item = find_item(product_name, headers)
        if item:
            message = get_response(tracker,
                f"You have {item.get('quantity')} units of {item.get('name')} in stock.",
                f"आपके पास {item.get('name')} के {item.get('quantity')} यूनिट स्टॉक में हैं।"
            )
        else:
            message = get_response(tracker,
                f"Sorry, I couldn't find an item named '{product_name}'.",
                f"क्षमा करें, मुझे '{product_name}' नाम का कोई आइटम नहीं मिला।"
            )
        
        dispatcher.utter_message(text=message)
        return [SlotSet("product_name", None)]

class ActionCheckItemDetails(Action):
    def name(self) -> Text:
        return "action_check_item_details"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        headers = get_auth_headers(tracker)
        if not headers:
            message = get_response(tracker, "Authentication error.", "प्रमाणीकरण त्रुटि।")
            dispatcher.utter_message(text=message)
            return []

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        if not product_name:
            message = get_response(tracker, "Which product would you like details for?", "आप किस उत्पाद का विवरण चाहते हैं?")
            dispatcher.utter_message(text=message)
            return []
            
        item = find_item(product_name, headers)
        if item:
            details_en = f"Here are the details for {item.get('name')}:\n- SKU: {item.get('sku')}\n- Category: {item.get('category')}\n- Supplier: {item.get('supplier')}\n- Selling Price: ₹{item.get('selling_price')}"
            details_hi = f"{item.get('name')} के विवरण यहाँ दिए गए हैं:\n- SKU: {item.get('sku')}\n- श्रेणी: {item.get('category')}\n- आपूर्तिकर्ता: {item.get('supplier')}\n- बिक्री मूल्य: ₹{item.get('selling_price')}"
            message = get_response(tracker, details_en, details_hi)
        else:
            message = get_response(tracker, f"Sorry, I couldn't find '{product_name}'.", f"क्षमा करें, मुझे '{product_name}' नहीं मिला।")

        dispatcher.utter_message(text=message)
        return [SlotSet("product_name", None)]

class ActionLowStock(Action):
    def name(self) -> Text:
        return "action_low_stock"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        headers = get_auth_headers(tracker)
        if not headers:
            message = get_response(tracker, "Authentication error. Please restart the chat.", "प्रमाणीकरण त्रुटि। कृपया चैट को पुनरारंभ करें।")
            dispatcher.utter_message(text=message)
            return []

        try:
            response = requests.get(f"{API_BASE_URL}/reports/low-stock/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = data.get('totalLowStockItems')
                message = get_response(tracker,
                    f"You currently have {count} items that are low on stock.",
                    f"आपके पास वर्तमान में {count} आइटम हैं जो स्टॉक में कम हैं।"
                )
            else:
                message = get_response(tracker, "I couldn't retrieve the low stock report right now.", "मैं अभी कम स्टॉक रिपोर्ट प्राप्त नहीं कर सका।")
        except Exception:
            message = get_response(tracker, "Sorry, something went wrong while fetching the report.", "क्षमा करें, रिपोर्ट लाते समय कुछ गड़बड़ हो गई।")

        dispatcher.utter_message(text=message)
        return []


class ActionSalesReport(Action):
    def name(self) -> Text:
        return "action_sales_report"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        headers = get_auth_headers(tracker)
        if not headers:
            message = get_response(tracker, "Authentication error. Please restart the chat.", "प्रमाणीकरण त्रुटि। कृपया चैट को पुनरारंभ करें।")
            dispatcher.utter_message(text=message)
            return []
        try:
            today_res = requests.get(f"{API_BASE_URL}/reports/sales/?range=today", headers=headers)
            week_res = requests.get(f"{API_BASE_URL}/reports/sales/?range=last7days", headers=headers)
            month_res = requests.get(f"{API_BASE_URL}/reports/sales/?range=last30days", headers=headers)

            if not all(r.status_code == 200 for r in [today_res, week_res, month_res]):
                 raise Exception("One or more report requests failed.")

            today_data = today_res.json()
            week_data = week_res.json()
            month_data = month_res.json()

            report_en = (
                f"Here is your sales summary:\n"
                f"- **Today**: You had {today_data['numberOfSales']} sales with a total revenue of ₹{today_data['totalRevenue']:.2f}.\n"
                f"- **Last 7 Days**: You had {week_data['numberOfSales']} sales with a total revenue of ₹{week_data['totalRevenue']:.2f}.\n"
                f"- **Last 30 Days**: You had {month_data['numberOfSales']} sales with a total revenue of ₹{month_data['totalRevenue']:.2f}."
            )
            
            report_hi = (
                f"यहाँ आपकी बिक्री का सारांश है:\n"
                f"- **आज**: आपकी {today_data['numberOfSales']} बिक्री हुई और कुल राजस्व ₹{today_data['totalRevenue']:.2f} था।\n"
                f"- **पिछले 7 दिन**: आपकी {week_data['numberOfSales']} बिक्री हुई और कुल राजस्व ₹{week_data['totalRevenue']:.2f} था।\n"
                f"- **पिछले 30 दिन**: आपकी {month_data['numberOfSales']} बिक्री हुई और कुल राजस्व ₹{month_data['totalRevenue']:.2f} था।"
            )
            
            message = get_response(tracker, report_en, report_hi)

        except Exception as e:
            print(f"ActionSalesReport Error: {e}")
            message = get_response(tracker, "Sorry, I couldn't generate the full sales report right now.", "क्षमा करें, मैं अभी पूरी बिक्री रिपोर्ट नहीं बना सका।")

        dispatcher.utter_message(text=message)
        return []


class ActionAddStock(Action):
    def name(self) -> Text:
        return "action_add_stock"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        headers = get_auth_headers(tracker)
        if not headers:
            dispatcher.utter_message(text=get_response(tracker, "Authentication error.", "प्रमाणीकरण त्रुटि।"))
            return []

        prod_name = next(tracker.get_latest_entity_values("product_name"), tracker.get_slot("product_name"))
        quantity = next(tracker.get_latest_entity_values("number"), tracker.get_slot("quantity"))

        if not prod_name:
            dispatcher.utter_message(text=get_response(tracker, "Which product do you want to add stock to?", "आप किस उत्पाद में स्टॉक जोड़ना चाहते हैं?"))
            return []

        item = find_item(prod_name, headers)
        if not item:
            dispatcher.utter_message(text=get_response(tracker, f"Product '{prod_name}' not found.", f"उत्पाद '{prod_name}' नहीं मिला।"))
            return []

        if not quantity:
            dispatcher.utter_message(text=get_response(tracker, "How many units to add?", "कितनी इकाइयां जोड़नी हैं?"))
            return [SlotSet("product_name", item['name'])]

        try:
            response = requests.post(
                f"{API_BASE_URL}/items/{item['id']}/adjust_stock/",
                headers=headers,
                json={'quantity_change': int(quantity), 'description': 'Added via chatbot'}
            )
            if response.status_code == 200:
                new_quantity = response.json().get('quantity')
                message = get_response(tracker, f"Done. The new stock for {item['name']} is {new_quantity}.", f"हो गया। {item['name']} का नया स्टॉक {new_quantity} है।")
            else:
                message = get_response(tracker, "Sorry, I failed to add the stock.", "क्षमा करें, मैं स्टॉक जोड़ने में विफल रहा।")
        except Exception:
            message = get_response(tracker, "An error occurred while updating stock.", "स्टॉक अपडेट करते समय एक त्रुटि हुई।")
        
        dispatcher.utter_message(text=message)
        return [SlotSet("product_name", None), SlotSet("quantity", None)]


class ActionRemoveStock(Action):
    def name(self) -> Text:
        return "action_remove_stock"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        headers = get_auth_headers(tracker)
        if not headers:
            dispatcher.utter_message(text=get_response(tracker, "Authentication error.", "प्रमाणीकरण त्रुटि।"))
            return []
        
        prod_name = next(tracker.get_latest_entity_values("product_name"), tracker.get_slot("product_name"))
        quantity_to_remove = next(tracker.get_latest_entity_values("number"), tracker.get_slot("quantity"))

        if not prod_name:
            dispatcher.utter_message(text=get_response(tracker, "Which product's stock do you want to remove?", "आप किस उत्पाद का स्टॉक हटाना चाहते हैं?"))
            return []

        item = find_item(prod_name, headers)
        if not item:
            dispatcher.utter_message(text=get_response(tracker, f"Product '{prod_name}' not found.", f"उत्पाद '{prod_name}' नहीं मिला।"))
            return []

        if not quantity_to_remove:
            dispatcher.utter_message(text=get_response(tracker, "How many units do you want to remove?", "आप कितनी इकाइयां हटाना चाहते हैं?"))
            return [SlotSet("product_name", item['name'])]

        if item['quantity'] < int(quantity_to_remove):
            message = get_response(tracker, f"Not enough stock. You only have {item['quantity']} units.", f"पर्याप्त स्टॉक नहीं है। आपके पास केवल {item['quantity']} इकाइयां हैं।")
            dispatcher.utter_message(text=message)
            return [SlotSet("product_name", None), SlotSet("quantity", None)]

        try:
            response = requests.post(
                f"{API_BASE_URL}/items/{item['id']}/adjust_stock/",
                headers=headers,
                json={'quantity_change': -int(quantity_to_remove), 'description': 'Removed via chatbot'}
            )
            if response.status_code == 200:
                new_quantity = response.json().get('quantity')
                message = get_response(tracker, f"Done. The new stock for {item['name']} is {new_quantity}.", f"हो गया। {item['name']} का नया स्टॉक {new_quantity} है।")
            else:
                message = get_response(tracker, "Sorry, I failed to remove the stock.", "क्षमा करें, मैं स्टॉक हटाने में विफल रहा।")
        except Exception:
            message = get_response(tracker, "An error occurred while updating stock.", "स्टॉक अपडेट करते समय एक त्रुटि हुई।")

        dispatcher.utter_message(text=message)
        return [SlotSet("product_name", None), SlotSet("quantity", None)]

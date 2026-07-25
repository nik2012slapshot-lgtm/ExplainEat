import argparse
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import cv2
from PIL import Image, ImageTk
import tempfile
from explain_eat.auth import login_user, register_user
from explain_eat.config import UserProfile
from explain_eat.recognition import recognize_food
from explain_eat.nutrition import analyze_nutrition
from explain_eat.explain import explain_meal
from explain_eat.personalization import create_user_profile


def parse_manual_food_input(raw_input: str) -> list[str]:
    items = []
    for line in raw_input.splitlines():
        entry = line.strip()
        if not entry:
            continue

        if "," in entry:
            items.append(entry)
        elif "-" in entry:
            items.append(entry)
        else:
            items.append(f"{entry}, 1 portion")

    return items


def launch_gui() -> None:
    window = tk.Tk()
    window.title("ExplainEat - AI Nutrition Analysis")
    window.geometry("960x750")
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    login_frame = ttk.Frame(window, padding=16)
    main_frame = ttk.Frame(window, padding=16)

    for frame in (login_frame, main_frame):
        frame.grid(row=0, column=0, sticky="nsew")

    welcome_label = ttk.Label(main_frame, text="", font=(None, 14, "bold"))
    welcome_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

    fields = [
        ("Age", "30"),
        ("Weight (kg)", "70.0"),
        ("Activity", "moderate"),
        ("Goal", "health"),
        ("Allergies (comma separated)", ""),
    ]
    entries = {}

    for idx, (label_text, default_value) in enumerate(fields, start=1):
        label = ttk.Label(main_frame, text=label_text)
        label.grid(row=idx, column=0, sticky="w", pady=4)
        entry = ttk.Entry(main_frame, width=30)
        entry.insert(0, default_value)
        entry.grid(row=idx, column=1, columnspan=2, sticky="ew", pady=4)
        entries[label_text] = entry

    camera_label = ttk.Label(main_frame, text="📸 Camera live feed:")
    camera_label.grid(row=len(fields) + 1, column=0, columnspan=3, sticky="w", pady=(12, 0))

    camera_frame = tk.Frame(main_frame, width=300, height=225, bg="black")
    camera_frame.grid(row=len(fields) + 2, column=0, columnspan=3, sticky="nsew", pady=(4, 8))
    main_frame.rowconfigure(len(fields) + 2, weight=1)

    camera_label_widget = tk.Label(camera_frame, text="", bg="black")
    camera_label_widget.pack(fill=tk.BOTH, expand=True)

    cap = None
    last_frame = None

    def update_camera():
        nonlocal cap, last_frame
        try:
            if cap is None:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    camera_label_widget.config(text="Camera not available", foreground="red")
                    try:
                        capture_button.config(state=tk.DISABLED)
                    except Exception:
                        pass
                    # Retry after 2s
                    camera_label_widget.after(2000, update_camera)
                    return
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (300, 225))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                last_frame = frame_rgb
                img = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image=img)
                camera_label_widget.config(image=photo)
                camera_label_widget.image = photo
                camera_label_widget.after(30, update_camera)
                try:
                    capture_button.config(state=tk.NORMAL)
                except Exception:
                    pass
            else:
                # No frame received, retry
                camera_label_widget.after(200, update_camera)
        except Exception as e:
            print(f"Camera error: {e}")
            camera_label_widget.config(text=f"Error: {str(e)[:30]}", foreground="red")


    def capture_photo():
        nonlocal last_frame
        if last_frame is None:
            camera_status.config(text="No frame to save.", foreground="red")
            return
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            img = Image.fromarray(last_frame)
            img.save(temp_file.name)
            temp_file.close()
            camera_status.config(text="Photo saved and being analyzed...", foreground="blue")
            analyze_with_image(temp_file.name)
        except Exception as e:
            camera_status.config(text=f"Error while saving: {e}", foreground="red")

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=len(fields) + 3, column=0, columnspan=3, sticky="ew", pady=(4, 0))

    capture_button = ttk.Button(button_frame, text="📸 Take photo & analyze", command=capture_photo)
    capture_button.pack(side=tk.LEFT, padx=2)

    # Start the camera loop only after the button exists (button is disabled if no camera)
    update_camera()

    camera_status = ttk.Label(button_frame, text="", foreground="blue")
    camera_status.pack(side=tk.LEFT, padx=8)

    food_label = ttk.Label(main_frame, text="Or enter a meal manually:")
    food_label.grid(row=len(fields) + 4, column=0, columnspan=3, sticky="w", pady=(12, 0))

    food_text = ScrolledText(main_frame, width=80, height=3, wrap=tk.WORD)
    food_text.grid(row=len(fields) + 5, column=0, columnspan=3, sticky="nsew", pady=(4, 8))

    result_text = ScrolledText(main_frame, width=80, height=10, wrap=tk.WORD)
    result_text.grid(row=len(fields) + 6, column=0, columnspan=3, pady=(12, 0), sticky="nsew")
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(len(fields) + 6, weight=1)

    def show_main_frame(username: str) -> None:
        welcome_label.config(text=f"🤖 Logged in as {username} | ExplainEat AI")
        login_frame.grid_remove()
        main_frame.grid()

    def login_callback() -> None:
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if not username or not password:
            login_status.config(text="Please enter username and password.")
            return

        if login_user(username, password):
            login_status.config(text="Login successful.")
            show_main_frame(username)
        else:
            login_status.config(text="Login failed. Please check your details.")

    def register_callback() -> None:
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if not username or not password:
            login_status.config(text="Please enter username and password.")
            return

        try:
            created = register_user(username, password)
        except ValueError:
            login_status.config(text="Username and password must not be empty.")
            return

        if created:
            login_status.config(text="Registration successful. Please log in.")
        else:
            login_status.config(text="This username is already taken.")

    username_label = ttk.Label(login_frame, text="Username")
    username_label.grid(row=0, column=0, sticky="w", pady=4)
    username_entry = ttk.Entry(login_frame, width=36)
    username_entry.grid(row=0, column=1, sticky="ew", pady=4)

    password_label = ttk.Label(login_frame, text="Password")
    password_label.grid(row=1, column=0, sticky="w", pady=4)
    password_entry = ttk.Entry(login_frame, show="*", width=36)
    password_entry.grid(row=1, column=1, sticky="ew", pady=4)

    login_status = ttk.Label(login_frame, text="", foreground="red")
    login_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 12))

    login_button = ttk.Button(login_frame, text="Login", command=login_callback)
    login_button.grid(row=3, column=0, sticky="ew", pady=4)
    register_button = ttk.Button(login_frame, text="Register", command=register_callback)
    register_button.grid(row=3, column=1, sticky="ew", pady=4)

    def analyze_callback() -> None:
        try:
            age = int(entries["Age"].get().strip())
            weight = float(entries["Weight (kg)"].get().strip())
            activity = entries["Activity"].get().strip()
            goal = entries["Goal"].get().strip()
            allergies = [item.strip() for item in entries["Allergies (comma separated)"].get().split(",") if item.strip()]
        except ValueError:
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, "Please enter valid values for age and weight.\n")
            return

        profile = create_user_profile(
            age=age,
            weight=weight,
            activity_level=activity,
            goal=goal,
            allergies=allergies,
        )

        manual_items = parse_manual_food_input(food_text.get("1.0", tk.END))
        detected_items = recognize_food(None, manual_items=manual_items)
        nutrition_report = analyze_nutrition(detected_items, profile)
        explanations = explain_meal(nutrition_report, profile)

        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "🔍 Analysis result:\n\n")
        result_text.insert(tk.END, "Detected foods:\n")
        for item in detected_items:
            result_text.insert(tk.END, f"- {item['name']} ({item['portion']})\n")

        result_text.insert(tk.END, "\nNutrition analysis:\n")
        result_text.insert(tk.END, f"Calories: {nutrition_report['macros']['calories']} kcal\n")
        result_text.insert(tk.END, f"Protein: {nutrition_report['macros']['protein_g']} g\n")
        result_text.insert(tk.END, f"Fat: {nutrition_report['macros']['fat_g']} g\n")
        result_text.insert(tk.END, f"Carbohydrates: {nutrition_report['macros']['carbs_g']} g\n")
        result_text.insert(tk.END, f"Fiber: {nutrition_report['macros']['fiber_g']} g\n")
        result_text.insert(tk.END, f"Sugar: {nutrition_report['macros']['sugar_g']} g\n")

        result_text.insert(tk.END, "\n💡 Explanations:\n")
        for line in explanations:
            result_text.insert(tk.END, f"- {line}\n")

    def analyze_with_image(image_path: str) -> None:
        try:
            age = int(entries["Age"].get().strip())
            weight = float(entries["Weight (kg)"].get().strip())
            activity = entries["Activity"].get().strip()
            goal = entries["Goal"].get().strip()
            allergies = [item.strip() for item in entries["Allergies (comma separated)"].get().split(",") if item.strip()]
        except ValueError:
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, "Please enter valid values for age and weight.\n")
            return

        profile = create_user_profile(
            age=age,
            weight=weight,
            activity_level=activity,
            goal=goal,
            allergies=allergies,
        )

        detected_items = recognize_food(image_path=image_path)
        nutrition_report = analyze_nutrition(detected_items, profile)
        explanations = explain_meal(nutrition_report, profile)

        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "🔍 AI analysis result:\n\n")
        result_text.insert(tk.END, "Detected foods:\n")
        for item in detected_items:
            confidence = item.get("confidence", "?")
            result_text.insert(tk.END, f"- {item['name']} ({item['portion']}) [{confidence}%]\n")

        result_text.insert(tk.END, "\nNutrition analysis:\n")
        result_text.insert(tk.END, f"Calories: {nutrition_report['macros']['calories']} kcal\n")
        result_text.insert(tk.END, f"Protein: {nutrition_report['macros']['protein_g']} g\n")
        result_text.insert(tk.END, f"Fat: {nutrition_report['macros']['fat_g']} g\n")
        result_text.insert(tk.END, f"Carbohydrates: {nutrition_report['macros']['carbs_g']} g\n")
        result_text.insert(tk.END, f"Fiber: {nutrition_report['macros']['fiber_g']} g\n")
        result_text.insert(tk.END, f"Sugar: {nutrition_report['macros']['sugar_g']} g\n")

        result_text.insert(tk.END, "\n💡 Explanations:\n")
        for line in explanations:
            result_text.insert(tk.END, f"- {line}\n")

    analyze_button = ttk.Button(main_frame, text="🔍 Start manual analysis", command=analyze_callback)
    analyze_button.grid(row=len(fields) + 7, column=0, columnspan=3, pady=(4, 0), sticky="ew")

    main_frame.grid_remove()
    login_frame.grid()

    def on_closing():
        if cap is not None:
            cap.release()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ExplainEat - AI-powered nutrition analysis with camera."
    )
    parser.add_argument("--gui", action="store_true", help="Launch the graphical interface with AI")
    parser.add_argument("--age", type=int, default=30, help="Age in years")
    parser.add_argument("--weight", type=float, default=70.0, help="Weight in kg")
    parser.add_argument(
        "--activity",
        choices=["low", "moderate", "high"],
        default="moderate",
        help="Activity level",
    )
    parser.add_argument(
        "--goal",
        choices=["health", "muscle", "weight_loss"],
        default="health",
        help="Personal goal",
    )
    parser.add_argument(
        "--allergies",
        nargs="*",
        default=[],
        help="Common intolerances or allergies",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Path to a food photo"
    )
    parser.add_argument(
        "--food",
        nargs="*",
        default=[],
        help="Manually entered foods"
    )
    parser.add_argument(
        "--username",
        type=str,
        default="guest",
        help="Username for CLI login"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="",
        help="Password for CLI login"
    )

    args = parser.parse_args()

    if args.gui:
        launch_gui()
        return

    if args.username != "guest" and args.password:
        if login_user(args.username, args.password):
            print(f"Logged in as {args.username}")
        else:
            print("Login failed. Continuing in guest mode.")

    user_profile = create_user_profile(
        age=args.age,
        weight=args.weight,
        activity_level=args.activity,
        goal=args.goal,
        allergies=args.allergies,
    )

    food_items = args.food if args.food else []
    detected_items = recognize_food(args.image, manual_items=food_items)
    nutrition_report = analyze_nutrition(detected_items, user_profile)
    explanations = explain_meal(nutrition_report, user_profile)

    print("🤖 ExplainEat AI analysis starting ...")
    print("\nDetected foods:")
    for item in detected_items:
        print(f"- {item['name']} ({item['portion']})")

    print("\nNutrition analysis:")
    for key, value in nutrition_report.items():
        print(f"{key}: {value}")

    print("\n💡 Explanations:")
    for line in explanations:
        print(f"- {line}")


if __name__ == "__main__":
    main()

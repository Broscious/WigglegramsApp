import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from PIL import Image, ImageTk, ImageFile
import datetime
import os
import numpy as np
import cv2

from pathlib import Path

import math

ImageFile.LOAD_TRUNCATED_IMAGES = True


class PhotoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.photos = []
        self.points = []
        self.current_photo_index = 0
        self.folder_path = str(Path.home())
        self.ratio = 16/9

        self.rotate = (
            tk.BooleanVar()
        )  # Add a variable to hold the state of the checkbox
        self.upload_photo_button = tk.Button(
            self.root, text="Upload Photo", command=self.upload_photo
        )
        self.upload_photo_button.pack()
        self.upload_folder_button = tk.Button(
            self.root, text="Upload Folder", command=self.upload_folder
        )
        self.upload_folder_button.pack()
        self.rotate_checkbox = tk.Checkbutton(  # Add a checkbox for rotation
            self.root, text="Rotate", variable=self.rotate
        )
        self.rotate_checkbox.pack()
        self.next_button = tk.Button(
            self.root, text="Next", state=tk.DISABLED, command=self.next_photo
        )
        self.next_button.pack()
        self.prev_button = tk.Button(
            self.root, text="Previous", state=tk.DISABLED, command=self.prev_photo
        )
        self.prev_button.pack()
        self.generate_button = tk.Button(
            self.root,
            text="Generate",
            state=tk.DISABLED,
            command=self.ask_frame_duration,
        )
        self.generate_button.pack()
        self.reset_button = tk.Button(self.root, text="Reset", command=self.reset)
        self.reset_button.pack()
        self.root.bind("<Left>", self.prev_photo)
        self.root.bind("<Right>", self.next_photo)

        # Create a frame to hold the photo previews
        self.preview_frame = tk.Frame(self.root)
        self.preview_frame.pack()

    def upload_photo(self):
        filepaths = filedialog.askopenfilenames()
        if len(filepaths) + len(self.photos) > 4:
            print("Maximum 4 photos can be uploaded.")
            return
        for filepath in filepaths:
            date = datetime.datetime.now()
            self.photos.append((filepath, date))
        self.photos.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
        if len(self.photos) > self.current_photo_index:
            self.open_photo(self.photos[self.current_photo_index][0])
        self.update_previews()  # Update the photo previews

    def upload_folder(self):
        folderpath = filedialog.askdirectory()
        self.folder_path = folderpath
        filepaths = [
            os.path.join(folderpath, f)
            for f in os.listdir(folderpath)
            if f.endswith(".jpg") or f.endswith(".png")
        ]
        if len(filepaths) + len(self.photos) > 4:
            print("Maximum 4 photos can be uploaded.")
            return
        for filepath in filepaths:
            date = datetime.datetime.now()
            self.photos.append((filepath, date))
        self.photos.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
        if len(self.photos) > self.current_photo_index:
            self.open_photo(self.photos[self.current_photo_index][0])
        self.update_previews()  # Update the photo previews

    def update_previews(self):  # Add a function to update the photo previews
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        for i, (filepath, date) in enumerate(self.photos):
            img = Image.open(filepath)
            img = img.resize((100, 100))  # Resize the image
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(
                self.preview_frame, image=photo, borderwidth=2, relief="solid"
            )  # Add a border around the frame
            label.image = photo
            label.pack(side=tk.LEFT)
            label.bind(
                "<Button-1>", lambda e, i=i: self.switch_photo(i)
            )  # Bind the click event to switch the photo
            label_number = tk.Label(
                self.preview_frame, text=str(i + 1)
            )  # Add a number for each preview frame
            label_number.pack(side=tk.LEFT)

    def switch_photo(self, index):
        self.current_photo_index = index
        self.open_photo(self.photos[self.current_photo_index][0])

    def open_photo(self, filepath):
        if hasattr(self, "canvas"):
            self.canvas.destroy()

        self.img = Image.open(filepath)
        self.original_img_size = self.img.size

        screen_width, screen_height = (
            self.root.winfo_screenwidth() / 1.3,
            self.root.winfo_screenheight() / 1.3,
        )
        ratio = min(screen_width / self.img.width, screen_height / self.img.height)
        self.img = self.img.resize(
            (int(self.img.width * ratio), int(self.img.height * ratio))
        )
        photo = ImageTk.PhotoImage(self.img)
        self.canvas = tk.Canvas(
            self.root, width=self.img.size[0], height=self.img.size[1]
        )
        self.canvas.create_image(0, 0, image=photo, anchor="nw")
        self.canvas.image = photo
        self.canvas.bind("<Button-1>", self.select_point)
        self.canvas.bind("<Motion>", self.show_magnifier)
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.canvas.pack()
        if len(self.photos) > 1:
            self.next_button.config(state=tk.NORMAL)
        if len(self.points) > self.current_photo_index:
            point = self.points[self.current_photo_index]
            event = tk.Event()
            event.x = point[0] * (self.canvas.winfo_width() / self.original_img_size[0])
            event.y = point[1] * (
                self.canvas.winfo_height() / self.original_img_size[1]
            )
            self.select_point(event)

    def show_magnifier(self, event):
        if hasattr(self, "magnifier"):
            self.canvas.delete(self.magnifier)
        magnifier_size = 200
        magnified_img = self.img.crop(
            (
                event.x - magnifier_size // 2,
                event.y - magnifier_size // 2,
                event.x + magnifier_size // 2,
                event.y + magnifier_size // 2,
            )
        ).resize((magnifier_size * 2, magnifier_size * 2))
        self.magnifier = ImageTk.PhotoImage(magnified_img)
        self.canvas.create_image(event.x, event.y, image=self.magnifier)
        if hasattr(self, "point"):
            point_x = self.point[0] * (
                self.canvas.winfo_width() / self.original_img_size[0]
            )
            point_y = self.point[1] * (
                self.canvas.winfo_height() / self.original_img_size[1]
            )
            if (
                abs(event.x - point_x) <= magnifier_size // 2
                and abs(event.y - point_y) <= magnifier_size // 2
            ):
                if hasattr(self, "point_text"):
                    self.canvas.delete(self.point_text)
                self.point_text = self.canvas.create_text(
                    event.x + (point_x - event.x) * 2,
                    event.y + (point_y - event.y) * 2,
                    text="x",
                    fill="red",
                )

    def zoom_image(self, event):
        if event.delta > 0:
            self.canvas.scale("all", 0, 0, 1.1, 1.1)
        else:
            self.canvas.scale("all", 0, 0, 0.9, 0.9)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def select_point(self, event):
        if hasattr(self, "point"):
            self.canvas.delete(self.point_text)
        self.point = (
            event.x * (self.original_img_size[0] / self.canvas.winfo_width()),
            event.y * (self.original_img_size[1] / self.canvas.winfo_height()),
        )
        print("Selected point:", self.point)
        self.point_text = self.canvas.create_text(
            event.x, event.y, text="x", fill="red"
        )
        if len(self.points) > self.current_photo_index:
            self.points[self.current_photo_index] = self.point
        else:
            self.points.append(self.point)

    def confirm_point(self):
        if hasattr(self, "point"):
            if len(self.points) > self.current_photo_index:
                self.points[self.current_photo_index] = self.point
            else:
                self.points.append(self.point)
            print(f"Number of poitns", len(self.points))
            if len(self.points) >= 3:
                self.generate_button.config(state=tk.NORMAL)

    def next_photo(self, event=None):
        self.confirm_point()
        if self.current_photo_index < len(self.photos) - 1:
            self.current_photo_index += 1
            self.open_photo(self.photos[self.current_photo_index][0])
            self.prev_button.config(state=tk.NORMAL)
        if self.current_photo_index == len(self.photos) - 1:
            self.next_button.config(state=tk.DISABLED)

    def prev_photo(self, event=None):
        if self.current_photo_index > 0:
            self.current_photo_index -= 1
            self.open_photo(self.photos[self.current_photo_index][0])
            self.next_button.config(state=tk.NORMAL)
        if self.current_photo_index == 0:
            self.prev_button.config(state=tk.DISABLED)

    def ask_frame_duration(self):
        self.frame_duration = simpledialog.askinteger(
            "Input", "Enter frame duration (in ms):", parent=self.root
        )
        self.align_and_generate()

    def align_and_generate(self):
        print(f"points are", self.points)
        if len(self.points) < 2:
            print("Not enough points to align.")
            return

        transformed_images = []
        
        # Align the images on the selected points while also constraining all images to overlapping area after they are aligned by translating the top left of the fully overlapping rectangle to 0,0
        min_left = min(point[0] for point in self.points)
        min_up = min(point[1] for point in self.points)
        ref_point = np.array((min_left, min_up), dtype="float32")

        for i, (path, date) in enumerate(self.photos):
            img = cv2.imread(path)
            original_height, original_width = img.shape[:2]

            selected_point = np.array(self.points[i], dtype="float32")

            dx, dy = ref_point - selected_point
            dx = round(dx)
            dy = round(dy)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            print("i", i, "dx", dx, "dy", dy, "original_height", original_height, "original_width", original_width)
            transformed_img = cv2.warpAffine(
                img,
                M,
                (img.shape[1], img.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
            )

            # constrain back to the new area
            valid_x_start = max(0, dx)
            valid_y_start = max(0, dy) 
            valid_x_end = min(original_width, original_width + dx)
            valid_y_end = min(original_height, original_height + dy)
            transformed_img = transformed_img[valid_y_start:valid_y_end, valid_x_start:valid_x_end]

            if self.rotate.get():  # Check if the rotate checkbox is checked
                transformed_img = cv2.rotate(
                    transformed_img, cv2.ROTATE_90_COUNTERCLOCKWISE
                )  # Rotate the image

            transformed_images.append(transformed_img)

        min_height = min(image.shape[0] for image in transformed_images)
        min_width = min(image.shape[1] for image in transformed_images)
        print("min height", min_height, "min_width", min_width)

        # constrain to largest area which can hit the desired aspect ratio
        # if height/width greater than ratio, truncate height else truncate width
        if min_height/min_width > self.ratio:
            print("cropping height")
            left, right = 0, min_width
            # calculate the new height by applying the ratio on the unchanging dimension
            output_height = math.ceil(min_width * self.ratio)
            half_height = output_height//2

            # get the top and bottom even if one is out of bounds
            top = round(ref_point[1]) - half_height
            bottom = round(ref_point[1]) + half_height

            # add any length that overruns out of the top/bottom bounds onto the other side
            bottom, top = bottom - max(top-min_width,0), top - min(bottom,0)

            # constrain to be within the actual bounds
            top = max(top, 0)
            bottom = min(bottom, min_height)
        else:
            print("cropping width")
            top, bottom = 0, min_height
            # calculate the new height by applying the ratio on the unchanging dimension
            output_width = math.ceil(min_height/self.ratio)

            # get the left and right even if one bound is out of bounds 
            half_width = output_width//2
            left = round(ref_point[0]) - half_width
            right = round(ref_point[0]) + half_width

            # add any length that overruns out of the left/right bounds onto the other side
            left, right = left - max(right-min_width,0), right - min(left,0)

            # constrain to be within the actual bounds 
            left = max(left, 0)
            right = min(right, min_width)

        print("left", left, "right", right, "top", top, "bottom", bottom)

        transformed_images = [image[top:bottom, left:right] for image in transformed_images]
        self.create_gif(transformed_images)

    def create_gif(self, images):
        gif_images = [
            Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) for img in images
        ]
        gif_images += gif_images[-2:0:-1]
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        gif_path = self.folder_path + f"/generated_{timestamp}.gif"
        gif_images[0].save(
            gif_path,
            save_all=True,
            append_images=gif_images[1:],
            duration=self.frame_duration,
            loop=0,
        )
        print("GIF saved at:", gif_path)

    def reset(self):
        self.photos = []
        self.points = []
        self.current_photo_index = 0
        if hasattr(self, "canvas"):
            self.canvas.delete("all")
        print("All photos, points, and canvas have been cleared.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PhotoApp()
    app.run()

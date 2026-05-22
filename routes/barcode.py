import cv2
from pyzbar import pyzbar

def decode_barcode(frame):
    """
    Detects and decodes barcodes from the given image frame.
    Returns the decoded barcode data as a list of tuples containing the barcode type and data.
    """
    # Load the image
    image = cv2.imread(frame)

    # Decode the barcodes in the image
    barcodes = pyzbar.decode(image)

    # Extract and return the barcode data
    barcode_data_list = []
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        barcode_data_list.append((barcode_type, barcode_data))

    return barcode_data_list

def read_from_image(image_path):
    """
    Reads an image from the specified path and decodes any barcodes present in it.
    Returns the decoded barcode data as a list of tuples containing the barcode type and data.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found at path: {image_path}")
        decoded_image = decode_barcode(image)
        cv2.imshow("Barcode Reader - Image", decoded_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Error reading image: {e}")
        return []
    return decode_barcode(image_path)

def read_from_webcam():
    """
    Captures video from the webcam and decodes any barcodes present in the video stream.
    Displays the video feed with detected barcodes highlighted.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame from webcam.")
            break

        decoded_frame = decode_barcode(frame)

        # Display the video feed with detected barcodes
        for barcode in decoded_frame:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = f"{barcode.type}: {barcode.data.decode('utf-8')}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("Barcode Reader - Webcam", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Example usage:
    # To read from an image:
    # barcode_data = read_from_image("path_to_image.jpg")
    
    # To read from the webcam:
    read_from_webcam()
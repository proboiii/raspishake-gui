import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from ttkthemes import ThemedTk
from obspy import UTCDateTime
import threading
import queue
import logging
from datetime import datetime, timedelta

# Import the refactored logic
from time_sync import set_remote_time_utc
from data_acquisition import fetch_waveforms

class DateTimePicker(tk.Toplevel):
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.title("Select Date and Time")

        now = datetime.utcnow()
        try:
            dt_str = self.entry_widget.get()
            now = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

        self.year = tk.IntVar(value=now.year)
        self.month = tk.IntVar(value=now.month)
        self.day = tk.IntVar(value=now.day)
        self.hour = tk.IntVar(value=now.hour)
        self.minute = tk.IntVar(value=now.minute)
        self.second = tk.IntVar(value=now.second)

        frame = ttk.Frame(self)
        frame.pack(padx=10, pady=10)

        ttk.Label(frame, text="Year:").grid(row=0, column=0)
        ttk.Spinbox(frame, from_=1970, to=2100, textvariable=self.year, width=5).grid(row=0, column=1)
        ttk.Label(frame, text="Month:").grid(row=0, column=2)
        ttk.Spinbox(frame, from_=1, to=12, textvariable=self.month, width=3).grid(row=0, column=3)
        ttk.Label(frame, text="Day:").grid(row=0, column=4)
        ttk.Spinbox(frame, from_=1, to=31, textvariable=self.day, width=3).grid(row=0, column=5)

        ttk.Label(frame, text="Hour:").grid(row=1, column=0)
        ttk.Spinbox(frame, from_=0, to=23, textvariable=self.hour, width=3).grid(row=1, column=1)
        ttk.Label(frame, text="Minute:").grid(row=1, column=2)
        ttk.Spinbox(frame, from_=0, to=59, textvariable=self.minute, width=3).grid(row=1, column=3)
        ttk.Label(frame, text="Second:").grid(row=1, column=4)
        ttk.Spinbox(frame, from_=0, to=59, textvariable=self.second, width=3).grid(row=1, column=5)

        ttk.Button(self, text="Done", command=self.on_done).pack(pady=5)

    def on_done(self):
        dt_str = f"{self.year.get():04d}-{self.month.get():02d}-{self.day.get():02d}T{self.hour.get():02d}:{self.minute.get():02d}:{self.second.get():02d}"
        self.entry_widget.delete(0, tk.END)
        self.entry_widget.insert(0, dt_str)
        self.destroy()

class SeismicSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Seismic Suite")
        self.root.geometry("850x650")

        # Setup logging
        self.setup_logging()

        # Style
        style = ttk.Style()
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5)
        style.configure("TEntry", padding=5)
        style.configure("TLabelframe.Label", padding=5)

        # Queue for thread communication
        self.task_queue = queue.Queue()

        # Create a Notebook widget (for tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Create the tabs
        self.time_sync_tab = ttk.Frame(self.notebook)
        self.data_acquisition_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.time_sync_tab, text="Time Sync")
        self.notebook.add(self.data_acquisition_tab, text="Data Acquisition")

        # Populate the tabs
        self.create_time_sync_tab()
        self.create_data_acquisition_tab()

        # Start the queue processor
        self.root.after(100, self.process_queue)
        logging.info("Seismic Suite application started.")

    def setup_logging(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logging.basicConfig(filename="logs/seismicsuite.log",
                            level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")

    def process_queue(self):
        try:
            message = self.task_queue.get_nowait()
            # Messages are tuples: (function_to_call, *args)
            message[0](*message[1:])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def start_task(self, worker_func, *args):
        thread = threading.Thread(target=worker_func, args=args)
        thread.daemon = True
        thread.start()

    # --- Time Sync Tab ---
    def create_time_sync_tab(self):
        input_frame = ttk.LabelFrame(self.time_sync_tab, text="Connection Details", padding=(10, 5))
        input_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(input_frame, text="Host:").grid(row=0, column=0, sticky="w", pady=2)
        self.ts_host_entry = ttk.Entry(input_frame, width=30)
        self.ts_host_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.ts_host_entry.insert(0, "rs.local")
        ttk.Label(input_frame, text="Username:").grid(row=1, column=0, sticky="w", pady=2)
        self.ts_username_entry = ttk.Entry(input_frame, width=30)
        self.ts_username_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.ts_username_entry.insert(0, "myshake")
        ttk.Label(input_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=2)
        self.ts_password_entry = ttk.Entry(input_frame, show="*", width=30)
        self.ts_password_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.ts_password_entry.insert(0, "geofisikaitera")
        input_frame.columnconfigure(1, weight=1)
        self.set_time_button = ttk.Button(self.time_sync_tab, text="Set Remote Time to UTC", command=self.run_set_time)
        self.set_time_button.pack(pady=5)

        # Status Indicator
        self.ts_status_label = ttk.Label(self.time_sync_tab, text="Status: Idle", anchor="center")
        self.ts_status_label.pack(fill="x", padx=10, pady=5)
        output_frame = ttk.LabelFrame(self.time_sync_tab, text="Output", padding=(10, 5))
        output_frame.pack(padx=10, pady=(0, 10), expand=True, fill="both")
        self.ts_output_text = scrolledtext.ScrolledText(output_frame, width=70, height=10, wrap=tk.WORD)
        self.ts_output_text.pack(expand=True, fill="both")

    def run_set_time(self):
        logging.info("'Set Remote Time to UTC' button clicked.")
        host = self.ts_host_entry.get()
        username = self.ts_username_entry.get()
        password = self.ts_password_entry.get()
        if not all([host, username, password]):
            logging.error("Time sync input error: all fields are required.")
            messagebox.showerror("Input Error", "All fields are required.")
            return
        logging.info(f"Attempting to set time on {host} for user {username}.")
        self.set_time_button.config(state="disabled")
        self.update_ts_status("Running", "blue")
        self.ts_output_text.delete('1.0', tk.END)
        self.ts_output_text.insert(tk.INSERT, f"Attempting to connect to {host} and set time...\n\n")
        self.start_task(self.set_time_worker, host, username, password)

    def set_time_worker(self, host, username, password):
        try:
            result = set_remote_time_utc(host, username, password)
            logging.info(f"Time sync result for {host}: {result}")
            self.task_queue.put((self.update_ts_output, result))
        except Exception as e:
            logging.error(f"Time sync error for {host}: {e}", exc_info=True)
            self.task_queue.put((self.handle_error, "Time Sync Error", e))

    def update_ts_output(self, result):
        self.ts_output_text.insert(tk.END, result)
        self.set_time_button.config(state="normal")
        if "Error" in result:
            self.update_ts_status("Error", "red")
        else:
            self.update_ts_status("Connected", "green")

    def update_ts_status(self, status, color):
        self.ts_status_label.config(text=f"Status: {status}", foreground=color)

    # --- Data Acquisition Tab ---
    def create_data_acquisition_tab(self):
        input_frame = ttk.LabelFrame(self.data_acquisition_tab, text="Waveform Parameters", padding=(10, 5))
        input_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(input_frame, text="Host:").grid(row=0, column=0, sticky="w", pady=2)
        self.da_host_entry = ttk.Entry(input_frame, width=30)
        self.da_host_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.da_host_entry.insert(0, "rs.local")
        ttk.Label(input_frame, text="Port:").grid(row=1, column=0, sticky="w", pady=2)
        self.da_port_entry = ttk.Entry(input_frame, width=30)
        self.da_port_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.da_port_entry.insert(0, "16032")
        ttk.Label(input_frame, text="Network:").grid(row=2, column=0, sticky="w", pady=2)
        self.da_net_entry = ttk.Entry(input_frame, width=30)
        self.da_net_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.da_net_entry.insert(0, "AM")
        ttk.Label(input_frame, text="Station:").grid(row=3, column=0, sticky="w", pady=2)
        self.da_sta_entry = ttk.Entry(input_frame, width=30)
        self.da_sta_entry.grid(row=3, column=1, sticky="ew", padx=5)
        self.da_sta_entry.insert(0, "R1E3F")
        ttk.Label(input_frame, text="Location:").grid(row=4, column=0, sticky="w", pady=2)
        self.da_loc_entry = ttk.Entry(input_frame, width=30)
        self.da_loc_entry.grid(row=4, column=1, sticky="ew", padx=5)
        self.da_loc_entry.insert(0, "00")
        ttk.Label(input_frame, text="Channel:").grid(row=5, column=0, sticky="w", pady=2)
        self.da_cha_entry = ttk.Entry(input_frame, width=30)
        self.da_cha_entry.grid(row=5, column=1, sticky="ew", padx=5)
        self.da_cha_entry.insert(0, "EH*")
        
        # Start Time
        ttk.Label(input_frame, text="Start Time (UTC):").grid(row=6, column=0, sticky="w", pady=2)
        start_time_frame = ttk.Frame(input_frame)
        start_time_frame.grid(row=6, column=1, sticky="ew", padx=5)
        self.da_start_entry = ttk.Entry(start_time_frame, width=25)
        self.da_start_entry.pack(side="left", fill="x", expand=True)
        start_btn = ttk.Button(start_time_frame, text="...", width=3, command=lambda: self.open_datetime_picker(self.da_start_entry))
        start_btn.pack(side="left")

        # End Time
        ttk.Label(input_frame, text="End Time (UTC):").grid(row=7, column=0, sticky="w", pady=2)
        end_time_frame = ttk.Frame(input_frame)
        end_time_frame.grid(row=7, column=1, sticky="ew", padx=5)
        self.da_end_entry = ttk.Entry(end_time_frame, width=25)
        self.da_end_entry.pack(side="left", fill="x", expand=True)
        end_btn = ttk.Button(end_time_frame, text="...", width=3, command=lambda: self.open_datetime_picker(self.da_end_entry))
        end_btn.pack(side="left")

        # Set default times
        now = datetime.utcnow()
        start_time = now.strftime("%Y-%m-%dT%H:%M:%S")
        end_time = (now + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S")
        self.da_start_entry.insert(0, start_time)
        self.da_end_entry.insert(0, end_time)

        input_frame.columnconfigure(1, weight=1)
        button_frame = ttk.Frame(self.data_acquisition_tab)
        button_frame.pack(pady=5)
        self.get_waveforms_button = ttk.Button(button_frame, text="Get Waveforms", command=self.run_get_waveforms)
        self.get_waveforms_button.pack(side="left", padx=5)
        self.plot_waveforms_button = ttk.Button(button_frame, text="Plot Waveforms", command=self.plot_waveforms)
        self.plot_waveforms_button.pack(side="left", padx=5)
        output_frame = ttk.LabelFrame(self.data_acquisition_tab, text="Output", padding=(10, 5))
        output_frame.pack(padx=10, pady=(0, 10), expand=True, fill="both")
        self.da_output_text = scrolledtext.ScrolledText(output_frame, width=70, height=10, wrap=tk.WORD)
        self.da_output_text.pack(expand=True, fill="both")
        self.stream = None

    def open_datetime_picker(self, entry_widget):
        DateTimePicker(self.root, entry_widget)

    def run_get_waveforms(self):
        try:
            params = {
                "host": self.da_host_entry.get(), "port": int(self.da_port_entry.get()),
                "net": self.da_net_entry.get(), "sta": self.da_sta_entry.get(),
                "loc": self.da_loc_entry.get(), "cha": self.da_cha_entry.get(),
                "start_time": UTCDateTime(self.da_start_entry.get()),
                "end_time": UTCDateTime(self.da_end_entry.get())
            }
            self.get_waveforms_button.config(state="disabled")
            self.da_output_text.delete('1.0', tk.END)
            self.da_output_text.insert(tk.INSERT, f"Connecting to {params['host']}:{params['port']}...\n")
            self.start_task(self.get_waveforms_worker, params)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            self.get_waveforms_button.config(state="normal")

    def get_waveforms_worker(self, params):
        try:
            self.task_queue.put((self.update_da_output, f"Fetching waveforms for {params['net']}.{params['sta']}.{params['loc']}.{params['cha']}...\n"))
            stream = fetch_waveforms(params)
            self.task_queue.put((self.finish_get_waveforms, stream))
        except Exception as e:
            self.task_queue.put((self.handle_error, "Waveform Fetch Error", e))

    def finish_get_waveforms(self, stream):
        self.stream = stream
        self.da_output_text.insert(tk.INSERT, "Waveforms fetched successfully.\n")
        self.da_output_text.insert(tk.INSERT, str(self.stream) + "\n")
        self.get_waveforms_button.config(state="normal")
        output_file = filedialog.asksaveasfilename(defaultextension=".mseed", filetypes=[("MSEED files", "*.mseed")])
        if output_file:
            try:
                self.stream.write(output_file, format="MSEED")
                self.da_output_text.insert(tk.INSERT, f"Stream saved to {output_file}\n")
                logging.info(f"Stream successfully saved to {output_file}")
            except Exception as e:
                logging.error(f"Failed to save stream to {output_file}: {e}", exc_info=True)
                messagebox.showerror("File Save Error", f"Failed to save file: {e}")

    def update_da_output(self, text):
        self.da_output_text.insert(tk.INSERT, text)

    def plot_waveforms(self):
        if self.stream:
            self.stream.plot()
        else:
            messagebox.showinfo("No Data", "No waveform data to plot. Please fetch waveforms first.")

    def handle_error(self, title, error):
        messagebox.showerror(title, str(error))
        if title == "Time Sync Error":
            self.set_time_button.config(state="normal")
            self.update_ts_status("Disconnected", "red")
        elif title == "Waveform Fetch Error":
            self.get_waveforms_button.config(state="normal")
        else:
             self.get_waveforms_button.config(state="normal")
             self.set_time_button.config(state="normal")


if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = SeismicSuiteApp(root)
    root.mainloop()

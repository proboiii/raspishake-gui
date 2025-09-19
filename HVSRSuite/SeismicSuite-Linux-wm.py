import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from ttkthemes import ThemedTk
from obspy import UTCDateTime
import threading
import queue

# Import the refactored logic
from time_sync import set_remote_time_utc
from data_acquisition import fetch_waveforms

class SeismicSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Seismic Suite")
        self.root.geometry("850x650")

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
        output_frame = ttk.LabelFrame(self.time_sync_tab, text="Output", padding=(10, 5))
        output_frame.pack(padx=10, pady=(0, 10), expand=True, fill="both")
        self.ts_output_text = scrolledtext.ScrolledText(output_frame, width=70, height=10, wrap=tk.WORD)
        self.ts_output_text.pack(expand=True, fill="both")

    def run_set_time(self):
        host = self.ts_host_entry.get()
        username = self.ts_username_entry.get()
        password = self.ts_password_entry.get()
        if not all([host, username, password]):
            messagebox.showerror("Input Error", "All fields are required.")
            return
        self.set_time_button.config(state="disabled")
        self.ts_output_text.delete('1.0', tk.END)
        self.ts_output_text.insert(tk.INSERT, f"Attempting to connect to {host} and set time...\n\n")
        self.start_task(self.set_time_worker, host, username, password)

    def set_time_worker(self, host, username, password):
        try:
            result = set_remote_time_utc(host, username, password)
            self.task_queue.put((self.update_ts_output, result))
        except Exception as e:
            self.task_queue.put((self.handle_error, "Time Sync Error", e))

    def update_ts_output(self, result):
        self.ts_output_text.insert(tk.END, result)
        self.set_time_button.config(state="normal")

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
        ttk.Label(input_frame, text="Start Time (UTC):").grid(row=6, column=0, sticky="w", pady=2)
        self.da_start_entry = ttk.Entry(input_frame, width=30)
        self.da_start_entry.grid(row=6, column=1, sticky="ew", padx=5)
        self.da_start_entry.insert(0, "2024-01-01T00:00:00")
        ttk.Label(input_frame, text="End Time (UTC):").grid(row=7, column=0, sticky="w", pady=2)
        self.da_end_entry = ttk.Entry(input_frame, width=30)
        self.da_end_entry.grid(row=7, column=1, sticky="ew", padx=5)
        self.da_end_entry.insert(0, "2024-01-01T00:01:00")
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
            self.stream.write(output_file, format="MSEED")
            self.da_output_text.insert(tk.INSERT, f"Stream saved to {output_file}\n")

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
        elif title == "Waveform Fetch Error":
            self.get_waveforms_button.config(state="normal")
        else:
             self.get_waveforms_button.config(state="normal")
             self.set_time_button.config(state="normal")


if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = SeismicSuiteApp(root)
    root.mainloop()

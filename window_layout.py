from tkinter import messagebox
from tkinter import ttk
import tkinter as tk
import ioh_backend
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib
matplotlib.use("TkAgg")


class tkinterApp(tk.Tk):

    def __init__(self, *args, **kwargs):

        self.mas = ioh_backend.MultiagentSystem()

        tk.Tk.__init__(self, *args, **kwargs)

        self.setup_fixed_items()

        self.setup_frame_container()

    def setup_fixed_items(self):
        self.frame_buttons = tk.Frame(self)
        self.frame_buttons.grid(row=0, column=0, sticky="nws", padx=5, pady=5)

        # self.button_update = tk.Button(self.frame_buttons, text="Update", command=lambda: self.)

        self.button_system_info = tk.Button(
            self.frame_buttons, text="System Info", command=lambda: self.show_frame(PageSystemInfo))
        self.button_system_info.grid(sticky="wen")

        self.button_graph = tk.Button(
            self.frame_buttons, text="Graph", command=lambda: self.show_frame(PageGraph))
        self.button_graph.grid(sticky="we")

        self.button_info = tk.Button(
            self.frame_buttons, text="Info", command=lambda: self.show_frame(PageAgentInfo))
        self.button_info.grid(sticky="we")

        self.frame_middle = tk.Frame(self)
        self.frame_middle.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.frame_logs = tk.Frame(
            self, highlightbackground="black", highlightthickness=1)
        self.frame_logs.grid(row=0, column=2, sticky="nes")

        self.label = tk.Label(self.frame_logs, text="SYSTEM LOGS")
        self.label.grid(sticky="w")

    def setup_frame_container(self):

        self.frames = {}

        # PageAgentMainWindow, PageEnergyTransactions, PageOptimization, PageOverview, PagePredictions, PageEnergyData, PageGraph,
        for new_frame in (PageSystemInfo, PageGraph, PageAgentInfo):

            frame = new_frame(self.frame_middle, self, self.mas)

            self.frames[new_frame] = frame

            frame.grid(row=0, column=0, sticky="nswe", padx=15, pady=15)

        self.show_frame(PageSystemInfo)

    def show_frame(self, desired_frame):
        frame = self.frames[desired_frame]
        frame.tkraise()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            try:
                self.mas.shutdown()
            except:
                pass
            finally:
                self.destroy()


class PageSystemInfo(tk.Frame):
    def __init__(self, parent, controller, multiagent_system, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.multiagent_system = multiagent_system

        self.label_system_active = tk.Label(
            self, text="System is ON")
        self.label_system_active.pack()

        self.button_start_script = tk.Button(
            self, text="Start Script", command=lambda: multiagent_system.run_auction_script())
        self.button_start_script.pack(fill=tk.X)

        self.button_kill_server = tk.Button(
            self, text="Kill Server", command=lambda: multiagent_system.shutdown())
        self.button_kill_server.pack(fill=tk.X)

        self.label_active_time = tk.Label(
            self, text="Active for 00:00:00")
        self.label_active_time.pack()

        self.update_labels()

    def update_labels(self):
        try:
            agents = self.multiagent_system.nameserver.agents()
            system_is_on = "ON" if len(agents) > 0 else "OFF"
            self.label_system_active.configure(
                text=f"System is {system_is_on}")
            self.after(1000, self.update_labels)
        except:
            pass


class PageGraph(tk.Frame):
    def __init__(self, parent, controller, multiagent_system, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.multiagent_system = multiagent_system

        # the figure that will contain the plot
        self.graph_figure = Figure(figsize=(5, 5),
                                   dpi=100)

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.graph_figure,
                                        master=self)
        self.canvas.draw()

        # placing the canvas on the Tkinter window
        # self.canvas.get_tk_widget().pack()

        # creating the Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas,
                                            self)
        self.toolbar.update()

        # placing the toolbar on the Tkinter window
        self.canvas.get_tk_widget().pack()
        self.update_graph()

    def update_graph(self):

        # adding the subplot
        self.plot1 = self.graph_figure.add_subplot(111)

        # plotting the graph
        for attributes in self.multiagent_system.agent_attributes:
            self.plot1.plot(attributes)

        self.canvas.draw()

        self.after(1000, self.update_graph)


class PageAgentInfo(tk.Frame):
    def __init__(self, parent, controller, multiagent_system):
        tk.Frame.__init__(self, parent)
        self.labels_active_agents = []

        self.label_title_agents = tk.Label(self, text="SYSTEM AGENTS")
        self.label_title_agents.pack()

        self.display_active_agents(multiagent_system)

    def display_active_agents(self, multiagent_system):
        for agent in self.labels_active_agents:
            agent.destroy()

        try:
            self.active_agents = multiagent_system.nameserver.agents()

            for agent in self.active_agents:
                new_active_agent = ttk.Label(
                    self, text=f"(ON) {agent}: WAITING")
                self.labels_active_agents.append(new_active_agent)
                new_active_agent.pack(fill=tk.X)
            self.after(1000, lambda: self.display_active_agents(
                multiagent_system))
        except:
            return

    # Driver Code


if __name__ == "__main__":
    app = tkinterApp()
    app.title("Agent Monitoring System")
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    app.mainloop()

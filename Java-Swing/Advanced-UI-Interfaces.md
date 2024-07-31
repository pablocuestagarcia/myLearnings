Certainly! Let's explore these advanced Java Swing topics with detailed examples and explanations. We will cover custom painting with JPanel, handling events and actions, integrating JMenuBar for creating menus, optimizing GUI performance with multithreading, and best practices for designing complex and responsive GUIs.

### 1. Custom Painting with JPanel

Custom painting in Swing is done by overriding the `paintComponent` method of a `JPanel`. This allows you to draw shapes, text, images, and more.

```java
import javax.swing.*;
import java.awt.*;

public class CustomPaintingPanel extends JPanel {

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        // Cast to Graphics2D for more advanced operations
        Graphics2D g2d = (Graphics2D) g;

        // Set rendering hints for better graphics quality
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        // Draw a filled rectangle
        g2d.setColor(Color.RED);
        g2d.fillRect(10, 10, 100, 50);

        // Draw a string
        g2d.setColor(Color.BLACK);
        g2d.setFont(new Font("Arial", Font.BOLD, 20));
        g2d.drawString("Custom Painting", 10, 100);

        // Draw an oval
        g2d.setColor(Color.BLUE);
        g2d.drawOval(120, 10, 100, 50);
    }

    public static void main(String[] args) {
        JFrame frame = new JFrame("Custom Painting Example");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.add(new CustomPaintingPanel());
        frame.setSize(300, 200);
        frame.setVisible(true);
    }
}
```

### 2. Handling Events and Actions

Swing provides various listeners to handle events like button clicks, mouse movements, and key presses. Here's an example of handling a button click event.

```java
import javax.swing.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class EventHandlingExample {
    public static void main(String[] args) {
        JFrame frame = new JFrame("Event Handling Example");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(300, 200);

        JButton button = new JButton("Click Me!");
        button.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                JOptionPane.showMessageDialog(frame, "Button Clicked!");
            }
        });

        frame.add(button);
        frame.setVisible(true);
    }
}
```

### 3. Integrating JMenuBar for Creating Menus

Menus are an essential part of many applications. Here's how to create a menu bar with menus and menu items.

```java
import javax.swing.*;

public class MenuExample {
    public static void main(String[] args) {
        JFrame frame = new JFrame("Menu Example");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(400, 300);

        JMenuBar menuBar = new JMenuBar();

        // Create File menu
        JMenu fileMenu = new JMenu("File");
        JMenuItem openItem = new JMenuItem("Open");
        JMenuItem saveItem = new JMenuItem("Save");
        JMenuItem exitItem = new JMenuItem("Exit");
        exitItem.addActionListener(e -> System.exit(0));

        fileMenu.add(openItem);
        fileMenu.add(saveItem);
        fileMenu.addSeparator();
        fileMenu.add(exitItem);

        // Add File menu to the menu bar
        menuBar.add(fileMenu);

        // Create Help menu
        JMenu helpMenu = new JMenu("Help");
        JMenuItem aboutItem = new JMenuItem("About");
        aboutItem.addActionListener(e -> JOptionPane.showMessageDialog(frame, "About this application"));

        helpMenu.add(aboutItem);

        // Add Help menu to the menu bar
        menuBar.add(helpMenu);

        frame.setJMenuBar(menuBar);
        frame.setVisible(true);
    }
}
```

### 4. Optimizing GUI Performance with Multithreading

To keep the GUI responsive, long-running tasks should not be run on the Event Dispatch Thread (EDT). SwingWorker is a useful class for this purpose.

```java
import javax.swing.*;

public class SwingWorkerExample {
    public static void main(String[] args) {
        JFrame frame = new JFrame("SwingWorker Example");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(400, 300);

        JButton startButton = new JButton("Start Task");
        JTextArea textArea = new JTextArea();

        startButton.addActionListener(e -> {
            SwingWorker<Void, String> worker = new SwingWorker<>() {
                @Override
                protected Void doInBackground() throws Exception {
                    for (int i = 1; i <= 10; i++) {
                        Thread.sleep(500); // Simulate long-running task
                        publish("Step " + i + " completed\n");
                    }
                    return null;
                }

                @Override
                protected void process(java.util.List<String> chunks) {
                    for (String chunk : chunks) {
                        textArea.append(chunk);
                    }
                }

                @Override
                protected void done() {
                    textArea.append("Task completed!\n");
                }
            };
            worker.execute();
        });

        frame.setLayout(new BorderLayout());
        frame.add(startButton, BorderLayout.NORTH);
        frame.add(new JScrollPane(textArea), BorderLayout.CENTER);
        frame.setVisible(true);
    }
}
```

### 5. Best Practices for Designing Complex and Responsive GUIs

#### Separate Model from Business Logic

Using the Model-View-Controller (MVC) pattern helps in separating the GUI (View) from the business logic (Controller) and the data (Model).

Here's a simple example:

```java
// Model
class CounterModel {
    private int count = 0;

    public int getCount() {
        return count;
    }

    public void increment() {
        count++;
    }
}

// View
import javax.swing.*;
import java.awt.*;

class CounterView extends JFrame {
    private final JLabel countLabel = new JLabel("0");
    private final JButton incrementButton = new JButton("Increment");

    public CounterView() {
        setTitle("MVC Example");
        setSize(200, 100);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new FlowLayout());

        add(countLabel);
        add(incrementButton);
    }

    public void setCount(int count) {
        countLabel.setText(String.valueOf(count));
    }

    public void addIncrementButtonListener(ActionListener listener) {
        incrementButton.addActionListener(listener);
    }
}

// Controller
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

class CounterController {
    private final CounterModel model;
    private final CounterView view;

    public CounterController(CounterModel model, CounterView view) {
        this.model = model;
        this.view = view;

        this.view.addIncrementButtonListener(new IncrementButtonListener());
    }

    class IncrementButtonListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            model.increment();
            view.setCount(model.getCount());
        }
    }
}

// Main
public class MVCExample {
    public static void main(String[] args) {
        CounterModel model = new CounterModel();
        CounterView view = new CounterView();
        new CounterController(model, view);

        view.setVisible(true);
    }
}
```

#### Use Layout Managers Effectively

Layout managers help in designing responsive and flexible GUIs. Combine layout managers to create complex layouts.

```java
import javax.swing.*;
import java.awt.*;

public class ComplexLayoutExample {
    public static void main(String[] args) {
        JFrame frame = new JFrame("Complex Layout Example");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(400, 300);

        JPanel mainPanel = new JPanel(new BorderLayout());

        JPanel topPanel = new JPanel(new FlowLayout());
        topPanel.add(new JLabel("Top Panel"));
        mainPanel.add(topPanel, BorderLayout.NORTH);

        JPanel centerPanel = new JPanel(new GridLayout(2, 2));
        centerPanel.add(new JButton("Button 1"));
        centerPanel.add(new JButton("Button 2"));
        centerPanel.add(new JButton("Button 3"));
        centerPanel.add(new JButton("Button 4"));
        mainPanel.add(centerPanel, BorderLayout.CENTER);

        JPanel bottomPanel = new JPanel(new FlowLayout());
        bottomPanel.add(new JLabel("Bottom Panel"));
        mainPanel.add(bottomPanel, BorderLayout.SOUTH);

        frame.add(mainPanel);
        frame.setVisible(true);
    }
}
```

#### Optimize for Performance

- Use `SwingWorker` for long-running tasks.
- Minimize the use of heavyweight components.
- Use `invokeLater` for GUI updates.

By following these practices and patterns, you can create robust, responsive, and maintainable Java Swing applications.
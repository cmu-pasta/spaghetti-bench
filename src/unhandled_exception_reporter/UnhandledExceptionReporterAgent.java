import java.lang.instrument.Instrumentation;

public class UnhandledExceptionReporterAgent {
    public static void premain(String agentArgs, Instrumentation inst) {
        Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
            @Override
            public void uncaughtException(Thread t, Throwable e) {
                System.err.println("Assertion failed: " + e.getMessage());
                System.exit(-1);
            }
        });
    }
}

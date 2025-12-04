package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/reorder_3_bad.c

public class Reorder3Bad {
    private static int iSet = 2;
    private static int iCheck = 1;

    private static volatile int a = 0;
    private static volatile int b = 0;

    public static void main(String[] args) {
        int i, err;
        a = 0;
        b = 0;

        Thread[] setPool = new Thread[iSet];
        Thread[] checkPool = new Thread[iCheck];

        for (i = 0; i < iSet; i++) {
            setPool[i] = new Thread(() -> {
                setThread();
            });
            setPool[i].start();
        }

        for (i = 0; i < iCheck; i++) {
            checkPool[i] = new Thread(() -> {
                checkThread();
            });
            checkPool[i].start();
        }

        for (i = 0; i < iSet; i++) {
            try {
                setPool[i].join();
            } catch (InterruptedException e) {
                System.err.println("pthread join error: " + e);
                throw new RuntimeException();
            }
        }

        for (i = 0; i < iCheck; i++) {
            try {
                checkPool[i].join();
            } catch (InterruptedException e) {
                System.err.println("pthread join error: " + e);
                throw new RuntimeException();
            }
        }
    }

    private static void setThread() {
        a = 1;
        b = -1;
    }

    private static void checkThread() {
        if (!((a == 0 && b == 0) || (a == 1 && b == -1))) {
            System.err.println("Bug found!");
            assert false;
        }
    }
}

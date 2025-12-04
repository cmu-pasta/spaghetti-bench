package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/token_ring_bad.c

import java.util.concurrent.atomic.*;

public class TokenRingBad {
    static int x1 = 1;
    static int x2 = 2; 
    static int x3 = 1;

    static AtomicBoolean flag1 = new AtomicBoolean(false);
    static AtomicBoolean flag2 = new AtomicBoolean(false);
    static AtomicBoolean flag3 = new AtomicBoolean(false);

    public static void main(String[] args) {
        Thread id1 = new Thread(() -> {
            synchronized (TokenRingBad.class) {
                x1 = (x3 + 1) % 4;
                flag1.set(true);
            }
        });

        Thread id2 = new Thread(() -> {
            synchronized (TokenRingBad.class) {
                x2 = x1;
                flag2.set(true);  
            }
        });

        Thread id3 = new Thread(() -> {
            synchronized (TokenRingBad.class) {
                x3 = x2;
                flag3.set(true);
            }
        });

        Thread id4 = new Thread(() -> {
            synchronized (TokenRingBad.class) {
                if (flag1.get() && flag2.get() && flag3.get()) {
                    assert (x1 == x2 && x2 == x3); /* BAD */
                }
            }
        });

        id1.start();
        id2.start();
        id3.start();
        id4.start();
    }
}
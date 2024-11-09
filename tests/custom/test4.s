    jeq $1, $0, done
    j 5
done:
    movi $1, 10
    lw $1, 6($0)
    jr $1
halt
.fill 65535
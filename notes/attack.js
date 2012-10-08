
function sniff(x)
{
    function p(x, min, max) {
        var a = false;
        var b = false;
        var c = false;

        var mid = ~~((min + max) / 2);
        if (x > mid) {
            a = true;
        } else if (x < mid) {
            b = true;
        } else {
            c = true;
        }

        var r;
        if (a == false && b == false) { // x == mid
            r = mid;
        }
        if (b == false && c == false) { // x > mid
            r = p(x, mid+1, max);
        }
        if (a == false && c == false) { // x < mid
            r = p(x, min, mid-1);
        }

        return r;
    }

    var r = [];
    for (i in x) {
        r += String.fromCharCode(p(x[i].charCodeAt(0), ' '.charCodeAt(0), '~'.charCodeAt(0)));
    }
    return r;
}

print (sniff("abcdefghijklmnopqrstuvwxyz"))

function addToCart(id, name, price) {
    event.preventDefault()

    fetch('/api/add-cart', {
        method: 'post',
        body: JSON.stringify({
            'id' : id,
            'name': name,
            'price': price
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(function(res){
        console.info(res)
        return res.json()
    }).then(function(data){
        console.info(data)

        let counter = document.getElementsByClassName('cartCounter')
        for (let i = 0; i < counter.length; i++) {
            counter[i].innerText = data.total_quantity
        }
    }).catch(function(err){
        console.error(err)
    })

}

function pay() {
    if(confirm('Bạn chắc chắn thanh toán không?') == true) {
        fetch('/api/pay', {
            method: 'post'
        }).then(function(res){
            console.info(res)
            return res.json()
        }).then(function(data){
            if (data.code == 200)
                alert('Thanh toán thành công')
                location.reload()
        }).catch(function(err){
            console.error(err)
        })
    }
}

function pay2() {
    if(confirm('Bạn chắc chắn muốn thanh toán không?') == true) {
        fetch('/api/pay2', {
            method: 'post'
        }).then(function(res){
            console.info(res)
            return res.json()
        }).then(function(data){
            if (data.code == 200)
                alert('Thanh toán thành công\n Mã hóa đơn của bạn là: ' + data.receipt + '\nHãy thanh toán trong: ' + data.time +' giờ tới' )
                location.reload()
        }).catch(function(err){
            console.error(err)
        })
    }
}


function addComment(productId){
    let content = document.getElementById('commentId')

    if (content !== null) {
        fetch('/api/comments', {
            method: 'post',
            body: JSON.stringify({
                'product_id': productId,
                'content': content.value
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(function(res){
            console.info(res)
            return res.json()
        }).then(function(data){
            if (data.status == 201){
                let c = data.comment

                let area = document.getElementById('commentArea')

                area.innerHTML = `
                    <div class="row comment">
                        <div class="col-md-1">
                            <img src="${c.user.avatar}" class="rounded-circle img-fluid"/>
                        </div>
                         <div class="col-md-11">
                             <p>${c.content}</p>
                             <p>
                                 ${c.created_date}
                             </p>
                        </div>
                    </div>
                    ` + area.innerHTML
                return c
            } else if (data.status == 404) {
                alert(data.err_msg)
            }

        }).catch(function(err){
            console.error(err)
        })
    }

    location.reload()
    location.reload()
}

function updateCart(id, obj) {
    fetch('/api/update-cart', {
            method: 'put',
            body: JSON.stringify({
                'id': id,
                'quantity': parseInt(obj.value)
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(function(res){
            console.info(res)
            return res.json()
        }).then(function(data){
            let counter = document.getElementsByClassName('cartCounter')
            for (let i = 0; i < counter.length; i++) {
                counter[i].innerText = data.total_quantity
            }

            let amount = document.getElementById('totalAmount')

            amount.innerText = data.total_amount
        }).catch(function(err){
            console.error(err)
        })
}


function deleteCart(id) {
    if (confirm("Bạn chắc chắn xóa sản phẩm này không") == true) {
        fetch('/api/delete-cart/' + id, {
            method: 'delete',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(function(res){
            console.info(res)
            return res.json()
        }).then(function(data){
            let counter = document.getElementsByClassName('cartCounter')
            for (let i = 0; i < counter.length; i++) {
                counter[i].innerText = data.total_quantity
            }

            let amount = document.getElementById('totalAmount')

            amount.innerText = data.total_amount

            let e = document.getElementById('product' + id)
            e.style.display = "none"
        }).catch(function(err){
            console.error(err)
        })
    }
}


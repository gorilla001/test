/**
 * Created by aidenZou on 15/9/28.
 */

/**
 * 事件系统
 * $on：在当前 vm 上监听一个事件。
 * $emit：只在当前 vm 上触发一个事件。
 * $dispatch：从当前的 vm 向上传递一个事件，一直到它的 $root 实例为止。如果传递过程中任意一个回调返回了 false ，那么事件会在该回调所属的实例处停止传播。
 * $broadcast：向当前 vm 的所有子 vm 向下广播该事件。广播会进行深度遍历。如果传递过程中一个回调返回了 false，那么该回调的所属实例就不会继续向下广播这个事件。
 * $once：在当前 vm 上为此事件绑定一个一次性的监听器。
 * $off：如果没有传递参数，那么停止监视所有事件；如果传递了一个事件，那么移除该事件的所有回调；如果事件和回调都被传递，则只移除该回调。
 */

// 方法
var util = {
    getCookie: function (c_name) {
        if (document.cookie.length > 0) {
            c_start = document.cookie.indexOf(c_name + "=");
            if (c_start != -1) {
                c_start = c_start + c_name.length + 1;
                c_end = document.cookie.indexOf(";", c_start);
                if (c_end == -1) c_end = document.cookie.length;
                return unescape(document.cookie.substring(c_start, c_end))
            }
        }
        return ""
    },
    setCookie: function (c_name, value, expiredays) {
        var exdate = new Date();
        exdate.setDate(exdate.getDate() + expiredays);
        document.cookie = c_name + "=" + escape(value) +
            ((expiredays == null) ? "" : "; expires=" + exdate.toGMTString())
    },
    checkCookie: function () {
        username = getCookie('username');
        if (username != null && username != "") {
            alert('Welcome again ' + username + '!')
        }
        else {
            username = prompt('Please enter your name:', "");
            if (username != null && username != "") {
                setCookie('username', username, 365)
            }
        }
    }
};

var app = {
    //apiDomain: 'http://192.168.1.100:9100'
    apiDomain: 'https://api.shequcun.com',
    //_xsrf: util.getCookie('_xsrf'),
    _xsrf: $('input[name="_xsrf"]').val(),
    uid: util.getCookie('uid'),
    user: {}
};

//购物车
//var cart = [];
var address_list;
var address_index = 0;

//Vue.config.debug = true; // 开启调试模式

// 插入分隔符
// 对于插入HTML，添加一个额外的最外层字符
// (% %) 是文本插值的标签
// 则 ((% %)) 是 HTML 插值的标签
Vue.config.delimiters = ['(%', '%)'];

Vue.http.options.emulateJSON = true;
Vue.http.headers.common['X-Xsrftoken'] = app._xsrf;
//Vue.http.transformResponse

//Vue.http.transforms.request.push(function (options) {
//    return options;
//});
//Vue.http.transforms.response.push(function (response) {
//    //console.log(response)
//    return response;
//});

//Vue.http.options.transformResponse = function (response) {
//    console.log(111111)
//    cosole.log(response)
//    return response;
//};

var fun = {
    errcodeFun: function (data) {
        if (!data) {
            return true;
        }
        if (data.errcode) {
            switch (data.errcode) {
                case 2001:  //用户未登录
                    //alert(data.errmsg);
                    //router.replace({
                    router.go({
                        name: 'login',
                        // params 和 query 可选
                        params: {
                            //goPath: 'address'   // 按钮跳转路径
                        }
                    });
                    break;
                default:
                    alert(data.errmsg);
            }
            return false;
        } else {
            return true;
        }
    },
    //保存用户基本信息
    set_user: function (_user) {
        app.user = _user;
        store.set('user', _user);
    },
    //获取用户基本信息
    get_user: function () {
        //TODO 优化(未登录)
        return app.user || store.get('user');
    },
    //保存用户地址
    set_address_list: function (_address_list) {
        address_list = _address_list;
    },
    //获取用户地址
    get_address_list: function () {
        if (undefined !== address_list) {
            return address_list;
        }
        return false;
    },
    get_address_list_ajax: function (callFun) {
        Vue.http.get('/api/address', {}, function (data, status, request) {
            fun.errcodeFun(data);
            fun.set_address_list(data);
            callFun(data)
        }).error(function (data, status, request) {
            // handle error
        });
    },
    //根据 id 获取对应地址
    get_address: function (id) {
        //TODO address_list可能为空
        if (!address_list) {

            console.warn('address_list为空')
            return {};
        }
        for (var i = 0; i < address_list.length; i++) {
            if (id == address_list[i].id) {

                console.log(address_list[i])
                return address_list[i];
            }
        }
    }
};

//var Foo = Vue.extend({
//    template: '<div class="foo">' +
//    '<h2>This is Foo!</h2>' +
//    '<router-view></router-view>' + // <- 嵌套的外链
//    '</div>'
//});

//var Load = Vue.extend({
//    template: '<div class="load">加载中</div>'
//});

//背景遮罩
Vue.component('c-dimmer', {
    props: ['active'],
    template: '<div class="c-dimmer" v-class="active : active" data-am-dimmer=""></div>'
});

//加载中组件
Vue.component('c-load', {
    props: ['hasShow'],
    template: '<div class="load" v-show="hasShow">加载中</div>'
});

//大文本输入框
Vue.component('c-textarea', {
    props: ['hasShow', 'text', 'btnText', 'placeholder'],
    //data: {
    //    placeholder: '请输入内容',   //文本框提示文字
    //    btnText: '确认',            //按钮显示文字
    //    //    goPath: 'address_detail'   // 按钮跳转路径
    //},
    template: '<div id="c-textarea" class="f-z" v-show="hasShow">' +
    '<textarea class="f-z-sm" rows="7" v-attr="placeholder:placeholder" v-model="text"></textarea>' +
    '<div class="btn-box"><button class="btn" v-on="click:save()">(% btnText %)</button></div>' +
    '</div>',
    methods: {
        save: function () {
            this.hasShow = false;
        }
    }
});

//底部购物车
Vue.component('c-bottom-buy', Vue.extend({
    data: function () {
        return {
            count: 1,
            type: 2
        }
    },
    created: function () {
        this.$on('return_recom_item', function () {
            this.$set('type', this.$parent.data.type);
        });
    },
    methods: {
        //reduce: function () {
        //    this.count > 0 && this.count--;
        //},
        //jia: function () {
        //    var recom_item = this.$parent.data;
        //    console.log(recom_item)
        //    console.log(recom_item.type)
        //    this.count++;
        //},
        buy: function () {
            var self = this;
            var recom_item = this.$parent.data;
            store.set('cart', [{
                id: recom_item.id,
                type: recom_item.type, //1.普通菜品，2.秒杀菜品
                img: recom_item.imgs[0],
                title: recom_item.title,
                price: recom_item.price,
                count: self.count
            }]);

            if (!app.user.id && !store.get('user') || !store.get('user').id) {  // 未登录
                router.go({
                    //router.replace({
                    name: 'login',
                    // params 和 query 可选
                    params: {}
                });
                return;
            }

            //去下单购买
            router.go({
                //router.replace({
                name: 'buy',
                params: {}
            })
        }
    },
    //v-attr="disabled: dis"\'disabled\'
    //template: '<div class="c-bottom-buy row-1"><div class="action"><button class="btn reduce" v-attr="disabled:count>1?false:true" v-on="click: count--">-</button><span class="count">(%count%)</span><button class="btn increase" v-on="click: count++">+</button></div><a class="btn add" v-link="{ path: \'/login\'}">登录</a><a class="btn add" v-on="click: buy()">立即购买</a></div>'
    //template: '<div class="c-bottom-buy row-1"><div class="action"><button class="btn reduce" v-attr="disabled:count>1?false:true" v-on="click: count--">-</button><span class="count">(%count%)</span><button class="btn increase" v-on="click: jia()">+</button></div><a class="btn add" v-on="click: buy()">立即购买</a></div>'
    template: '<div class="c-bottom-buy row-1"><div v-show="2==type"></div><div class="action" v-show="2!=type"><button class="btn reduce" v-attr="disabled:count>1?false:true" v-on="click: count--">━</button><span class="count">(%count%)</span><button class="btn increase" v-on="click: count++">╋</button></div><a class="btn add" v-on="click: buy()">立即购买</a></div>'
}));

var Index = Vue.extend({
    template: '#index-template',
    data: function () {
        return {
            //data: null,
            //nav_list: [
            //    '家装', '家政', '商超', '养老', '汽车',
            //    '汽车1', '汽车2', '汽车3', '汽车4', '汽车5', '汽车6', '汽车7', '汽车8', '汽车9', '汽车10', '汽车11', '汽车12', '汽车13', '汽车14'
            //],
            status: '',
            //nav_list: nav_list,
            ////nav_activity: '全部',
            //nav_activity: nav_list[0],

            list: []
        }
    },
    methods: {
        //getList: function (e, id) {
        getList: function (id) {
            //console.log(e)
            //console.log(id)
            //console.log(this.nav_activity)

            //if (id != this.nav_activity) {
            //    this.nav_activity = id;
            //    this.list = [];
            //}
            //
            //this.status = 'load';
            //
            //// ajax
            //// GET request
            //this.$http.get('/test/list.json', {id: this.nav_activity}, function (data, status, request) {
            //
            //    console.log(data)
            //    this.status = '';
            //    // set data on self
            //    //this.$set('list', this.list.concat(data))
            //    this.list = this.list.concat(data);
            //}).error(function (data, status, request) {
            //    // handle error
            //})
        }
    },
    created: function () {
        this.$http.get('/api/home', {page: 1}, function (data, status, request) {
            fun.errcodeFun(data);

            this.$set('recom_item_list', data.recom_item_list);

        }).error(function (data, status, request) {
            // handle error
        });
    },
    ready: function () {

    }
});

//单品详情
var RecomItem = Vue.extend({
    template: '#recom-item-template',
    data: function () {
        return {
            show_qr_code: false
        };
    },
    created: function () {
        var id = this.$route.params.id;
        this.$http.get('/api/recom_item', {id: id}, function (data, status, request) {

            this.status = '';
            // set data on vm
            this.$set('data', data);
            //this.$set('list', this.list.concat(data))
            //this.list = this.list.concat(data);

            setTimeout(function () {
                $('#slide').swipeSlide({
                    continuousScroll: true,
                    speed: 3000,
                    transitionType: 'cubic-bezier(0.22, 0.69, 0.72, 0.88)',
                    firstCallback: function (i, sum, me) {
                        me.find('.dot').children().first().addClass('cur');
                    },
                    callback: function (i, sum, me) {
                        me.find('.dot').children().eq(i).addClass('cur').siblings().removeClass('cur');
                    }
                });
            }, 500);

            this.$broadcast('return_recom_item');
        }).error(function (data, status, request) {
            // handle error
        });
    },
    ready: function () {
        //console.log('ready')
    },
    attached: function () {
        //console.log('attached')
    },
    methods: {
        buy: function () {
        }
    }
});

//购买页
var Buy = Vue.extend({
    template: '#buy-template',
    data: function () {
        return {
            address: {},            //收货地址
            cart_list: [],          //购物车
            memo: '',               //备注
            has_freight: false,     //是否有邮费
            freight: 10 * 100,      //运费
            limit: 99 * 100,        //减免运费界限
            all_price: 0,           //订单总价
            show_textarea: false    //是否显示大文本输入框组件
        }
    },
    created: function () {
        var cart = store.get('cart');
        if (!cart) {
            //购物车为空,去首页
            router.go({
                //router.replace({
                name: 'index',
                // params 和 query 可选
                params: {}
            });
            return;
        }
        this.$set('cart_list', cart);

        // 计算订单总价
        this.count_all_price();

        //var address_list = fun.get_address_list();
        //if (address_list) {
        //    vm.$set('address', address_list[address_index]);
        //    return;
        //}

        //fun.get_address_list_ajax(function (_address_list) {
        //    vm.$set('address', _address_list[address_index]);
        //});

        this.$on('return_address_list', function (_address_list) {
            this.$set('address', _address_list[address_index]);
        });
        this.$dispatch('get_address_list');
    },
    methods: {
        //输入备注
        input: function () {
            this.show_textarea = true;

            //store.set('InputData', {
            //    placeholder: '留言给农庄',   //文本框提示文字
            //    btnText: '确认',            //按钮显示文字
            //    goPath: 'buy',   // 按钮跳转路径
            //    params: {}
            //});
            //router.go({
            //    //router.replace({
            //    name: 'input',
            //    // params 和 query 可选
            //    params: {}
            //})
        },
        //计算订单总价
        count_all_price: function () {
            var cart_list = this.cart_list;
            var item;
            var all_price = 0;
            for (var i = 0; i < cart_list.length; i++) {
                item = cart_list[i];
                all_price = item.count * item.price;
                if (2 != item.type) {
                    this.has_freight = true;
                }
            }
            if (this.has_freight && all_price < this.limit) {
                all_price += this.freight;
            }
            //this.all_price = all_price;
            this.$set('all_price', all_price);
        },
        //创建订单
        created_order: function (type) {
            var self = this;

            //验证
            if (!self.address.id) {
                alert('请选择收货地址');
            }

            var params = {
                //combo_id: '',
                //combo_idx: '',
                //coupon_id: '',
                type: 3, //订单类型，取值 1.套餐订单 2.选菜订单, 3.单品订单
                //items: '',  //amount1,id2:amount2...
                //extras: '',
                //spares: '',
                name: self.address.name,
                mobile: self.address.mobile,
                address: self.address.address,
                memo: self.memo,
                paytype: 3   //支付方式，默认2，2.支付宝支付，3.微信支付
            };

            var extras = [];
            for (var index in self.cart_list) {
                var _item = self.cart_list[index];
                extras.push('' + _item.id + ':' + _item.count);
            }
            params.extras = extras.join(",");

            //提交订单
            this.$http.post('/api/order', params, function (data, status, request) {
                if (!fun.errcodeFun(data)) {
                    return;
                }
                if (self.all_price != data.fee) {
                    //TODO 金额计算错误
                    alert('金额计算错误');
                    return;
                }
                //清除购物车数据
                store.remove('cart');

                //TODO 去支付
                //console.log('去支付');
                //console.log(data);

                //去支付
                var url = '/pay/wx?orderno=' + data.orderno + '&type=1';
                //url += '&url=' + escape(window.location.host + '/#!pay_result');
                //console.log(url)
                window.location.href = url;

                //router.go({
                //    //router.replace({
                //    name: 'pay_result',
                //    // params 和 query 可选
                //    params: {}
                //})

            }).error(function (data, status, request) {
                // handle error
            });
        }
    }
});

//订单支付结果
var PayResult = Vue.extend({
    template: '#pay-result-template'
});

var Login = Vue.extend({
    template: '#login-template',
    data: function () {
        return {
            mobile: '',
            smscode: '',
            text: '获取验证码',
            remaintime: 60,
            has_disabled_send_smscode: false,
            djs: null
        };
    },
    created: function () {
    },
    methods: {
        sendSms: function () {
            var self = this;

            if (11 !== this.mobile.trim().length) {
                //alert('请输入正确手机号');
                return;
            }
            if (this.has_disabled_send_smscode) {
                return;
            }

            this.$http.post('/api/auth/send_smscode', {
                //_xsrf: app._xsrf,
                mobile: this.mobile
            }, function (data, status, request) {
                if (data && data.errcode) {
                    alert(data.errmsg);
                    return;
                }
                self.text = '(' + self.remaintime + 's)重新获取';
                self.has_disabled_send_smscode = true;

                self.djs = setInterval(function () {
                    //self.has_disabled_send_smscode = true;
                    self.remaintime--;
                    if (self.remaintime > 0) {
                        self.text = '(' + self.remaintime + 's)重新获取';
                    } else {
                        clearInterval(self.djs);
                        self.text = '获取验证码';
                        self.remaintime = 60;
                        self.has_disabled_send_smscode = false;
                    }
                }, 1000);
            }).error(function (data, status, request) {
                // handle error
            });

        },
        submit: function () {
            if (11 !== this.mobile.trim().length) {
                //alert('请输入正确手机号');
                return;
            }
            if (!this.smscode.trim().length) {
                //alert('请输入验证码');
                return;
            }
            this.$http.post('/api/auth/login', {
                //_xsrf: app._xsrf,
                mobile: this.mobile,
                smscode: this.smscode
            }, function (data, status, request) {
                if (data && data.errcode) {
                    alert(data.errmsg);
                    return;
                }

                fun.set_user(data.user);    // 保存用户基本信息
                fun.set_address_list(data.address_list); // 保存用户地址列表

                //router.go({
                router.replace({
                    name: 'buy',
                    // params 和 query 可选
                    params: {}
                })

            }).error(function (data, status, request) {
                // handle error
            });
        }
    }
});

//我的地址列表
var Address = Vue.extend({
    template: '#address-template',
    data: function () {
        return {
            address_list: []
        };
    },
    created: function () {
        var self = this;

        //var address_list = fun.get_address_list();
        //if (address_list) {
        //    self.$set('address_list', address_list);
        //    return;
        //}
        //
        //fun.get_address_list_ajax(function (_address_list) {
        //    self.$set('address_list', _address_list);
        //});

        this.$on('return_address_list', function (_address_list) {
            this.$set('address_list', _address_list);
        });
        this.$dispatch('get_address_list');
    },
    methods: {
        //选择地址
        selectAddress: function (address, index) {
            var address_list = fun.get_address_list();
            for (var i = 0; i < address_list.length; i++) {
                address_list[i].default = false;
            }
            address.default = true;

            address_index = index;
            //router.go({
            router.replace({
                name: 'buy',
                params: {}
            })
        },
        //编辑地址
        edit: function (address, index, e) {
            //router.replace({
            router.go({
                name: 'address_detail',
                params: {id: address.id}
                //params: {index: index}  //索引
            });
            e.stopPropagation();
        }
    }
});

//我的地址详情
var AddressDetail = Vue.extend({
    //template: '<p>Address</p>',
    template: '#address-detail-template',
    data: function () {
        return {
            address: {
                id: 0,// - 可选，地址id，修改地址时必传，若设置为默认小区，只需传id即可
                name: '',// - 姓名
                mobile: '',// - 手机号
                city: '北京',// - 城市
                region: '',// - 区域
                address: ''// - 地址
            }
        };
    },
    created: function () {
        //console.log(this)
        //console.log(this.path)
        //console.log(this.$route.params)
        //console.log(this.$route.query)

        //this.$on('a', function (data) {
        //    console.log(data);
        //});
        //this.$dispatch('b', {a: 1});

        //console.log(this.$root)
        //console.log(this.$root.a)
        //console.log(this.$root.b)

        //获取北京地区区县
        this.$http.jsonp(app.apiDomain + '/util/region', {pid: 1}, function (data, status, request) {
            this.$set('region_list', data.regions);

            this.$dispatch('get_address', this.address_id);

        }).error(function (data, status, request) {
            // handle error
        });

        // 当前地址 id
        this.address_id = this.$route.params.id;

        this.$on('return_address', function (_address) {
            this.address = _address;
            console.log(this.address)
        });

        //this.$dispatch('get_address', this.address_id);
    },
    methods: {
        input: function () {
            store.set('InputData', {
                placeholder: '请输入街道、小区名称',   //文本框提示文字
                btnText: '保存地址',            //按钮显示文字
                goPath: 'address_detail',   // 按钮跳转路径
                params: {id: this.address.id}
            });
            router.go({
                //router.replace({
                name: 'input',
                // params 和 query 可选
                params: {
                    //id: 1,
                    //placeholder: '请输入内容',   //文本框提示文字
                    //btnText: '确认',            //按钮显示文字
                    //goPath: 'address_detail'   // 按钮跳转路径
                }
            })
        },
        //选择地区
        select_region: function () {

        },
        //保存地址
        save: function () {
            this.$http.post('/api/address', this.address, function (data, status, request) {
                if (data && data.errcode) {
                    alert(data.errmsg);
                    return;
                }
                //保存成功

                //清除地址列表
                this.$dispatch('remove_address_list');

                router.go({
                    name: 'address',
                    // params 和 query 可选
                    params: {}
                })

            }).error(function (data, status, request) {
                // handle error
            });
        }
    }
});

//订单备注
var Memo = Vue.extend({
    //template: '<p>Address</p>',
    template: '#memo-template',
    data: function () {
        return {
            memo: '',
        };
    }
});

/**
 * 输入
 * 参数：
 * placeholder:文本框提示文字
 * btnText:按钮显示文字
 * goPath:按钮跳转路径
 * params:路由参数
 */
var Input = Vue.extend({
    template: '#input-template',
    //props: {
    //    placeholder: '请输入内容',   //文本框提示文字
    //    btnText: '确认',            //按钮显示文字
    //    goPath: 'address_detail'   // 按钮跳转路径
    //},
    //props: ['placeholder'],
    //props: ['placeholder', 'btnText', 'goPath'],
    data: function () {
        //return {
        //    placeholder: '请输入内容',   //文本框提示文字
        //    btnText: '确认',            //按钮显示文字
        //    goPath: 'address_detail'   // 按钮跳转路径
        //};

        var data = store.get('InputData');
        !data && console.warn('缺少必要参数！');
        return data;
    },
    methods: {
        submit: function () {
            //router.go({
            router.replace({
                name: this.goPath,
                params: this.params
            });
        }
    },
    created: function () {
        console.log(this)
        console.log(router)
    }
});

var App = Vue.extend({
    data: function () {
        return {
            a: 1,
            b: 2
        }
    },
    created: function () {
        //console.log('app created...')

        //this.$on('b', function (data) {
        //    console.log(data);
        //
        //    this.$broadcast('a', {a: 1});
        //})

        //保存用户地址
        this.$once('return_address_list', function (_address_list) {
            fun.set_address_list(_address_list);
        });

        //获取用户地址
        //this.$on('get_address_list', function (args) {
        this.$on('get_address_list', function () {
            if (!(undefined === address_list || null === address_list)) {
                this.$emit('return_address_list', address_list) && this.$broadcast('return_address_list', address_list);
                //args.on && this.$emit(args.on, args.param) && this.$broadcast(args.on, args.param);
                return false;
            }
            this.$http.get('/api/address', {}, function (data, status, request) {
                fun.errcodeFun(data);

                var address_list = data;

                this.$emit('return_address_list', address_list) && this.$broadcast('return_address_list', address_list);

                //callFun(data)
                return false;

            }).error(function (data, status, request) {
                // handle error
            });
        });

        //根据 id 获取对应地址
        this.$on('get_address', function (id) {
            if (!address_list) {
                console.warn('address_list为空');

                this.$once('return_address_list', function (_address_list) {
                    this.$emit('get_address', id);
                });

                this.$emit('get_address_list', {on: 'get_address', param: id});
                //this.$emit('get_address_list', [id, 'get_address']);
                return;
            }
            for (var i = 0; i < address_list.length; i++) {
                if (id == address_list[i].id) {
                    this.$broadcast('return_address', address_list[i]);
                }
            }
        });

        this.$on('remove_address_list', function () {
            address_list = null;
        });
    },
    compiled: function () {
        this.$broadcast('a', {a: 1});
    },
    ready: function () {
        this.$broadcast('a', {a: 1});
    }
});

var router = new VueRouter();

router.map({
    '/': {
        name: 'index',  // 路径别名
        component: Index
    },
    //推荐菜详情
    '/recomitem/:id': {
        name: 'recom_item_detail',
        component: RecomItem
    },
    //购买
    '/buy': {
        name: 'buy',
        component: Buy
    },
    //登录
    '/login': {
        name: 'login',
        component: Login
    },
    //地址列表
    '/address': {
        name: 'address',
        component: Address
    },
    //地址详情
    '/address/:id': {
        name: 'address_detail',
        component: AddressDetail
    },
    //订单支付结果
    '/pay_result': {
        name: 'pay_result',
        component: PayResult
    },
    //// 订单备注
    //'/memo': {
    //    component: Memo
    //},
    // 输入
    '/input': {
        name: 'input',
        component: Input
    },
    // not found handler
    '*': {
        //component: require('./components/not-found.vue')
        component: Index
    }
});

// redirect
router.redirect({
    //'/': '/list',
    //'/hello/:userId': '/user/:userId'
});

router.start(App, '#app');

//'/foo': {
//    component: Foo,
//    // 在/foo下设置一个子路由
//    subRoutes: {
//        '/bar': {
//            // 当匹配到/foo/bar时，会在Foo's <router-view>内渲染
//            // 一个Bar组件
//            component: Bar
//        },
//        //'/baz': {
//        //    // Baz也是一样，不同之处是匹配的路由会是/foo/baz
//        //    component: Baz
//        //}
//    }
//},


//Vue.component('demo-grid', {
//    template: '#grid-template',
//    replace: true,
//    props: ['data', 'columns', 'filter-key'],
//    data: function () {
//        return {
//            data: null,
//            columns: null,
//            sortKey: '',
//            filterKey: '',
//            reversed: {}
//        }
//    },
//    compiled: function () {
//        // initialize reverse state
//        var self = this
//        this.columns.forEach(function (key) {
//            self.reversed.$add(key, false)
//        })
//    },
//    methods: {
//        sortBy: function (key) {
//            this.sortKey = key
//            this.reversed[key] = !this.reversed[key]
//        }
//    }
//})
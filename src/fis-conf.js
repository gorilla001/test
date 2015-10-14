/**
 * Created by aidenZou on 15/9/19.
 */

//由于使用了bower，有很多非必须资源。通过set project.files对象指定需要编译的文件夹和引用的资源
//fis.set('project.files', ['page/**','map.json','modules/**','lib']);

// MD5
fis.match('*.{js,css,scss}', {
    useHash: true
});

fis.set('project.ignore', [
    //'output/**',
    'node_modules/**',
    '.git/**',
    '.svn/**',
    //'static/styles/**.less'
    'fis-conf.js',
    'package.json',
    'bower.json',
    'bower_components/**'
]);

fis.match('bower.json', {
    // 设置 release 为 FALSE，不再产出此文件
    release: false
});

// 所有的文件产出到 static/ 目录下
//fis.match('src/static/*', {
fis.match('/static/*', {
//fis.match('/**/*', {
//fis.match('*', {
    release: '/$0'
    //release: '/static/$0'
});

// 所有模板放到 tempalte 目录下
//fis.match('src/templates/*.html', {
//fis.match('/templates/*.html', {
//fis.match('/templates/*', {
fis.match('/*.html', {
    release: '/templates/$0'
});

fis.match('/bower_components/**/*.{js,css}', {
    release: '/static/$0'
});

//fis.match('*.{scss,less,map}', {
//fis.match('/static/style/**/*.scss}', {
//    release: false
//});

fis.match('/static/style/*.scss', {
//fis.match('/static/style/app.scss', {
    parser: fis.plugin('sass', {}), //属性 parser 表示了插件的类型
    rExt: '.css',
    postprocessor: fis.plugin('autoprefixer', {
        // detail config (https://github.com/postcss/autoprefixer#browsers)
        "browsers": ["Android >= 2.3", "ChromeAndroid > 1%", "iOS >= 4"],
        "cascade": true
    }),
    optimizer: fis.plugin('clean-css')
});

fis.match('/static/styles/*.less', {
    parser: fis.plugin('less'), // invoke `fis-parser-less`,
    rExt: '.css',
    postprocessor: fis.plugin('autoprefixer')
});

//fis.match('*.css', {
//    postprocessor: fis.plugin('autoprefixer', {
//        // detail config (https://github.com/postcss/autoprefixer#browsers)
//        "browsers": ["Android >= 2.3", "ChromeAndroid > 1%", "iOS >= 4"],
//        "cascade": true
//    })
//});

//fis.match('/src/bower_components/**/*', {
//    //release: '/static/bower_components/$0'
//    //release: '/static/bower_components/$0'
//    release: 'static/$0'
//});

//fis.match('/src/bower_components/angular/angular.min.js', {
//    //release: '/static/bower_components/$0'
//    //release: '/static/bower_components/$0'
//    release: '/static/bower_components/angular/$0'
//});

//// widget源码目录下的资源被标注为组件
//fis.match('/widget/**/*', {
//    isMod: true
//});
//
//// widget下的 js 调用 jswrapper 进行自动化组件化封装
//fis.match('/widget/**/*.js', {
//    postprocessor: fis.plugin('jswrapper', {
//        type: 'commonjs'
//    })
//});
//
///**
// * mock 假数据模拟
// */
//// test 目录下的原封不动产出到 test 目录下
////fis.match('/test/**/*', {
////    release: '$0'
////});
//
//fis.match('/test/**', {
//    release: '$0'
//});
//
//fis.match('/test/server.conf', {
//    release: '/config/server.conf'
//});
//
//
//// optimize
//fis.media('prod')
//    .match('*.js', {
//        optimizer: fis.plugin('uglify-js', {
//            mangle: {
//                expect: ['require', 'define', 'some string'] //不想被压的
//            }
//        })
//    })
//    .match('*.css', {
//        optimizer: fis.plugin('clean-css', {
//            'keepBreaks': true //保持一个规则一个换行
//        })
//    });
//
//// pack
//fis.media('prod')
//    // 启用打包插件，必须匹配 ::package
//    .match('::package', {
//        packager: fis.plugin('map'),
//        spriter: fis.plugin('csssprites', {
//            layout: 'matrix',
//            margin: '15'
//        })
//    })
//    .match('*.js', {
//        packTo: '/static/all_others.js'
//    })
//    .match('*.css', {
//        packTo: '/staitc/all_others.js'
//    })
//    .match('/widget/**/*.js', {
//        packTo: '/static/all_comp.js'
//    })
//    .match('/widget/**/*.css', {
//        packTo: '/static/all_comp.css'
//    });


/**********************生产环境下CSS、JS压缩合并*****************/
//使用方法 fis3 release prod
fis.media('prod')
    //注意压缩时.async.js文件是异步加载的，不能直接用annotate解析
    //.match('**!(.async).js', {
    //    preprocessor: fis.plugin('annotate'),
    //    optimizer: fis.plugin('uglify-js')
    //})
    //.match("lib/mod.js", {
    //    packTo: "/pkg/vendor.js"
    //})

    ////所有页面中引用到的bower js资源
    //.match("bower_components/**/*.js", {
    //    packTo: "/pkg/vendor.js"
    //})
    ////所有页面中引用到的bower css资源
    //.match("bower_components/**/*.css", {
    //    packTo: "/pkg/vendor.css"
    //});

    //.match('**!(.async).js', {
    .match('app.js', {
        //preprocessor: fis.plugin('annotate'),
        optimizer: fis.plugin('uglify-js')
    })
    //.match('**.css', {
    //    optimizer: fis.plugin('clean-css')
    //});


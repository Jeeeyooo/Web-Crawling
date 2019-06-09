'use strict';

//const database = require('./database');
//const sequelize = database.sequelize;

const serverless = require('serverless-http');

const express = require('express');
const app = express();

const exphbs= require('express-handlebars');
const bodyParser = require('body-parser');

const path = require('path');

const AWS = require('aws-sdk');
const mysql = require('mysql');



const pool = mysql.createPool({
    host : process.env.DB_HOST,
    user : process.env.DB_USER,
    password : process.env.DB_PW,
    database : process.env.DB_NAME,
    multipleStatements : true,
    connectionLimit : 20,
    waitForConnections : false 
});


app.locals.pretty = true;

app.set('view engine', 'pug');
app.set('views', path.join(__dirname, '/tmp/view'));
app.use(express.static(path.join(__dirname, '/tmp/public')));


const page_num = 400;



app.get('/', (req, res, next) => {

        // 페이지 값 들어오면 그대로 하고 없으면 1
        let page = req.query.page || 1;
        
        // 쿼리 값 들어오면 그대로 하고 없으면 없는대로
        let query = req.query.query || undefined;

        // 날짜 값 들어오면 그대로 하고 없으면 없는대로
        let s_date = req.query.s_date || undefined;
        let e_date = req.query.e_date || undefined;


        let sql1 = `SELECT COUNT(id) as total FROM news `;
        let sql2 = `SELECT query from news group by query `;

        let params1 = [];
        let params2 = [];

        // 뭐라도 들어옴 
        if( req.query != undefined ) {
            if (query) {
                sql1 = sql1 + 'WHERE query=?';
                params1.push(query);
            }
            /*
            if (s_date) {
                sql1 = sql1 + 'and DATE(date) >= ?';
                sql2 = sql2 + 'WHERE DATE(date) >= ?'; 
                params1.push(s_date);
                params2.push(s_date);
            }
            if (e_date) {
                sql1 = sql1 + 'DATE(date) <= ?';
                sql2 = sql2 + 'DATE(date) <= ?';
                params1.push(e_date);
                params2.push(e_date);
            }
            */
        }
        
        
        sql1 = sql1+';';
        sql2 = sql2+';';
        let params = params1.concat(params2);
        let sql = sql1+sql2;

        pool.getConnection( (err, conn) => {
                if(err) return next(err);
                

                console.log(sql);
                console.log(params);

                conn.query(sql, params, (err, datas, fields) => {
                        if(err) return next(err);
                        let total_page_num = Math.ceil(datas[0][0].total/page_num);
                        let queries = [];
                        datas[1].forEach( (data,index)=>{
                            queries.push(data.query);
                        });

                        let without_query = `SELECT title, query, url, summary, DATE_FORMAT(date, "%Y-%m-%d") as date  FROM news ORDER BY upload_date DESC LIMIT ?,?;`;
                        

                        let with_query = `SELECT title, query, url, summary, DATE_FORMAT(date, "%Y-%m-%d") as date FROM news WHERE query=? ORDER BY upload_date DESC LIMIT ?, ?`;

                        

                        let sql = query===undefined ? without_query : with_query;

                        let start = page_num*(page-1); 
            
                        let params = query===undefined ? [start, page_num] : [query, 0, page_num];

                        conn.query(sql, params, (err, datas, fields)=>{
                                conn.release();
                                console.log(sql);
                                console.log(datas);
                                if(err) return next(err);

                                return res.render('main', {datas: datas, total_page_num: total_page_num, queries: queries});
                                });
                        });

        });
        
});



// error handler
app.use(function(err, req, res, next) {

  if (!err.message)
    return res.json({'error':err});
  else if (err.message.indexOf('U_S_E_R')!=-1)
    return res.render('verify',{layout: false,result:"ERROR!"});
  else
    return res.json({'error' : err.message});
});

// catch 404 and forward to error handler
// 라우팅이 안되는 에러들은 여기서 해결
app.use(function(req, res, next) {
  return res.status(404).json({"error":"Not Found"});
});


module.exports.handler = serverless(app);
